# controllers/hacTripsExcel.py

import json
import xlrd
from enum import Enum
from datetime import datetime, timezone
import logging

from .. import app, db, models
from ..models import UploadFiles


# helper functions
# ================

def hac_date(date_str):
    # 08.01.2022 18:59:22
    return datetime.strptime(date_str, r'%d.%m.%Y %H:%M:%S')


# convert comma-decimal to floating point number
def hrk_value(num_str):
    return float(num_str.replace(',', '.'))


def humanize_time(amount):
    def process_time(amount):
        IVALS = [ 1,   60,  60*60 ] 
        NAMES = [ 's', 'm', 'h'   ]
        result = []

        for i in range(len(NAMES)-1, -1, -1):
            a = amount // IVALS[i]
            if a > 0: 
                result.append( (a, NAMES[i]) )
                amount -= a * IVALS[i]
        return result

    buf = ''
    for u in process_time(int(amount)):
        if u[0] > 0:
            buf += "%d%s " % (u[0], u[1])
    
    return buf.rstrip()



class HAC_Sheet(Enum):
    """ Stupci u worksheetu koji nas zanimaju """
    col_Relacija        = 1
    col_Tip_transakcije = 2
    col_Vrijeme_ulaska  = 4
    col_Vrijeme_izlaska = 5
    col_Uplata_HRK      = 8
    col_Isplata_HRK     = 9

class HAC_Sheet_Error(Exception):
    """Exception raised for errors while loading Trips Sheet

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message=f'Failed to load HAC Trips Sheet at "{{__name__}}"'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class HAC_Sheet_Object:
    def __init__(self, uploads_id, original_wb_fn, hashed_wb_fn):
        self.original_wb_fn = original_wb_fn
        self.hashed_wb_fn = hashed_wb_fn
        self.setUploadsId(uploads_id)
        self._worksheet = None
        self._header_rownum = None

    
    def __repr__(self):
        return f'<HAC_Sheet_Object {self.hashed_wb_fn!r}>'

    def setUploadsId(self, uploads_id):
        self.uploads_id = uploads_id
    
    def getUploadsId(self):
        return self.uploads_id

    def setWorksheet(self, worksheet):
        self._worksheet = worksheet

    def sheet_validate(self):
        """
        Excel sheet format validation
        -- returns rownum where real trip records start or None if some error
        -- although we could, we don't raise any exceptions since we want to 
            handle this error gracefully
        """
        self._header_rownum = None
        worksheet = self._worksheet

        app.logger.info("sheet_validate running ...")

        # Find where transactions begin
        for rownum in range(0, worksheet.nrows):
            if ('Relacija' == worksheet.cell_value(rownum, HAC_Sheet.col_Relacija.value)):
                self._header_rownum = rownum
                break

        if self._header_rownum is None:
            return
            raise HAC_Sheet_Error("Invalid data format")

        if False: # commented out
            for colnum in range(1, worksheet.ncols):
                if worksheet.cell_value(header_rownum, colnum):
                    print('Column {} = {}'.format(colnum, repr(worksheet.cell_value(header_rownum, colnum))))

        if (    worksheet.cell_value(self._header_rownum, HAC_Sheet.col_Tip_transakcije.value) == 'Tip transakcije' and
                worksheet.cell_value(self._header_rownum, HAC_Sheet.col_Vrijeme_ulaska.value)  == 'Vrijeme ulaska'  and
                worksheet.cell_value(self._header_rownum, HAC_Sheet.col_Vrijeme_izlaska.value) == 'Vrijeme izlaska' and
                worksheet.cell_value(self._header_rownum, HAC_Sheet.col_Uplata_HRK.value)      == 'Uplata (HRK)'    and
                worksheet.cell_value(self._header_rownum, HAC_Sheet.col_Isplata_HRK.value)     == 'Isplata (HRK)'   and
            True ):
            pass
        else:
            return
            raise HAC_Sheet_Error("Invalid data format")

        return self._header_rownum


    def sheet_process(self, json_out_fn=None):
        """
        We go through workbook looking for rows we're interested in
        - gets called after sheet_validate has prepared the 'self'
        """
        # pdb.set_trace()

        app.logger.info("hac_sheet_process running ...")

        uploads_id = self.getUploadsId()
        header_rownum = self._header_rownum
        worksheet = self._worksheet

        # tracking unique set of entry and exit points
        # (never seen before - missing from the model)
        missing_topo_ul = set() # entry points
        missing_topo_iz = set() # exit points
        missing_topo    = set() # whole record missing

        # create the JSON output file for writing
        of = None
        if json_out_fn:
            of = open(json_out_fn, 'w', encoding="utf-8")
            of.truncate()

            # write general information in a header record of the JSONL file
            ctm = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            json_obj = {
                "uploads_id": uploads_id,
                "original_filename": self.original_wb_fn,
                "local_filename": self.hashed_wb_fn,
                "processed_at": ctm
            }
            json.dump(json_obj, of, sort_keys=False)
            of.write('\n')

        # count of rows written
        row_out = 0

        # scan through the original sheet, find where toll'd transactions are
        for rownum in range(1 + header_rownum, worksheet.nrows):
            if 'Cestarina' == worksheet.cell_value(rownum, HAC_Sheet.col_Tip_transakcije.value):
                vr_ul_str = worksheet.cell_value(rownum, HAC_Sheet.col_Vrijeme_ulaska.value)
                vr_iz_str = worksheet.cell_value(rownum, HAC_Sheet.col_Vrijeme_izlaska.value)
                relacija  = worksheet.cell_value(rownum, HAC_Sheet.col_Relacija.value)
                [ od, do ] = relacija.split(' - ')
                toll_hrk = hrk_value(worksheet.cell_value(rownum, HAC_Sheet.col_Isplata_HRK.value))
                
                vr_ul_dt  = hac_date(vr_ul_str)
                vr_iz_dt  = hac_date(vr_iz_str)

                duration = (vr_iz_dt - vr_ul_dt).total_seconds()

                hac_od = models.mjesto_get_by_mjesto(od)
                hac_do = models.mjesto_get_by_mjesto(do)

                # these are overriden with looked up responses            
                hac_do_gps = None

                if hac_od is None:
                    hac_od_gps = None
                    if od not in missing_topo:
                        missing_topo.add(od)
                        app.logger.warning(f'Naplatna postaja "{od}" nije uvedena u HAC_Mjesto relaciju')
                else:
                    hac_od_gps = models.point_get_by_mjesto_port(hac_od, 'ulaz')
                    if hac_od_gps is None:
                        if od not in missing_topo_ul:
                            missing_topo_ul.add(od)
                            app.logger.warning(f'Naplatnoj postaji "{od}" nije navedena GPS točka \'ulaz\' (HAC_Point)')

                if hac_do is None:
                    hac_do_gps = None
                    if do not in missing_topo:
                        missing_topo.add(od)
                        app.logger.warning(f'Naplatna postaja "{do}" nije uvedena u HAC_Mjesto relaciju')
                else:
                    hac_do_gps = models.point_get_by_mjesto_port(hac_do, 'izlaz')
                    if hac_do_gps is None:
                        if do not in missing_topo_iz:
                            missing_topo_iz.add(do)
                            app.logger.warning(f'Naplatnoj postaji "{do}" nije navedena GPS točka \'izlaz\' (HAC_Point)')

                if hac_od_gps and hac_do_gps:
                    dist = models.routetab_get_distance(hac_od, hac_do)
                    dist_km = float(dist)/1000.0
                    avg_speed_kmh = dist_km/(duration/3600.0)
                else:
                    dist = None
                    dist_km = None
                    avg_speed_kmh = None

                # enter records in the TripRecords table
                try:
                    tr_id = models.triprecords_add(id_upload=uploads_id, id_mjesto_od=hac_od, id_mjesto_do=hac_do,
                        entered_at=vr_ul_dt, exited_at=vr_iz_dt, hac_toll_hrk=toll_hrk, status=1,
                        trip_length=int(dist), speed_avg_kmh=avg_speed_kmh)
                finally:
                    # write row to JSON output, with the following info fields added:
                    # duration - seconds, duration - human readable, dist_km, avg_speed_kmh
                    if of:
                        json_obj = {
                            "triprecords_id": tr_id,
                            "od": od,
                            "do": do, 
                            "od_gps": { "lon": float(hac_od_gps[0]), "lat": float(hac_od_gps[1])} if hac_od_gps else None,
                            "do_gps": { "lon": float(hac_do_gps[0]), "lat": float(hac_do_gps[1])} if hac_do_gps else None,
                            "vr_ulaz":  vr_ul_str,
                            "vr_izlaz": vr_iz_str,
                            "duration_sec": duration,
                            "duration_human": humanize_time(duration),
                            "dist_km": (float(format(dist_km, '.1f')) if dist_km is not None else None),
                            "avs_kmh": (float(format(avg_speed_kmh, '.1f')) if avg_speed_kmh is not None else None),
                            "toll_hrk": toll_hrk
                        }
                        json.dump(json_obj, of, sort_keys=False)
                        of.write('\n')
                    row_out += 1


        # end for
        if of:
            of.close()
            app.logger.info(f'Zapisano ukupno {row_out} slogova u izlaznu JSON datoteku "{json_out_fn}"')

        tr_count = models.triprecords_count(uploads_id)
        app.logger.info(f'Baza sad sadrzi {tr_count} slogova trip recorda')
        return tr_count


    # top level method, pulls all the internal ropes 
    # ==============================================
    def process_workbook(self, json_out_fn):
        # returns: number of TripRecords created from HAC Sheet
        tr_count = None

        # open the workbook and look at the first worksheet
        workbook = xlrd.open_workbook(self.hashed_wb_fn)
        self.setWorksheet(workbook.sheet_by_index(0))

        if self.sheet_validate():
            tr_count = self.sheet_process(json_out_fn)
        
        app.logger.info(f'Odradio process_hac_workbook na "{self.hashed_wb_fn}" - rezultat je u "{json_out_fn}", tr_count={tr_count}')
        return tr_count
