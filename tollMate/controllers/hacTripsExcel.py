# controllers/hacTripsExcel.py

import json
import xlrd
from enum import Enum
from datetime import datetime
import logging

from .. import app, db, models
from ..models import UploadFiles

def add_a_b(a, b):
    return a + b


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


def hac_sheet_validate(worksheet):
    """
    Excel sheet format validation
     -- returns rownum where real trip records start or None if some error
     -- although we could, we don't raise any exceptions since we want to 
           handle this error gracefully
    """
    header_rownum = None

    app.logger.info("hac_sheet_validate running ...")

    # Find where transactions begin
    for rownum in range(0, worksheet.nrows):
        if ('Relacija' == worksheet.cell_value(rownum, HAC_Sheet.col_Relacija.value)):
            header_rownum = rownum
            break

    if header_rownum is None:
        return
        raise HAC_Sheet_Error("Invalid data format")

    if False:
        for colnum in range(1, worksheet.ncols):
            if worksheet.cell_value(header_rownum, colnum):
                print('Column {} = {}'.format(colnum, repr(worksheet.cell_value(header_rownum, colnum))))

    if (    worksheet.cell_value(header_rownum, HAC_Sheet.col_Tip_transakcije.value) == 'Tip transakcije' and
            worksheet.cell_value(header_rownum, HAC_Sheet.col_Vrijeme_ulaska.value)  == 'Vrijeme ulaska'  and
            worksheet.cell_value(header_rownum, HAC_Sheet.col_Vrijeme_izlaska.value) == 'Vrijeme izlaska' and
            worksheet.cell_value(header_rownum, HAC_Sheet.col_Uplata_HRK.value)      == 'Uplata (HRK)'    and
            worksheet.cell_value(header_rownum, HAC_Sheet.col_Isplata_HRK.value)     == 'Isplata (HRK)'   and
        True ):
        return header_rownum
    else:
        return
        raise HAC_Sheet_Error("Invalid data format")

    return header_rownum


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


def hac_sheet_process(uf_id, worksheet, header_rownum, json_out_fn):
    """
    We go through workbook looking for rows we're interested in
    """
    # pdb.set_trace()

    app.logger.info("hac_sheet_process running ...")

    # tracking unique set of entry and exit points
    # (never seen before - missing from the model)
    missing_topo_ul = set() # entry points
    missing_topo_iz = set() # exit points
    missing_topo    = set() # whole record missing

    # create the JSON output file for writing
    of = open(json_out_fn, 'w', encoding="utf-8")
    of.truncate()

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

            # write row to JSON output, with the following info fields added:
            # duration - seconds, duration - human readable, dist_km, avg_speed_kmh
            json_obj = {
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

            # enter records in the TripRecords table
            models.triprecords_add(id_upload=uf_id, id_mjesto_od=hac_od, id_mjesto_do=hac_do,
                entered_at=vr_ul_dt, exited_at=vr_iz_dt, hac_toll_hrk=toll_hrk, status=1,
                trip_length=int(dist), speed_avg_kmh=avg_speed_kmh)

            row_out += 1

    # end for
    of.close()

    # TODO: izbaciti malo bogatiji summary na kraju, dodati zbirni redak u Excel
    app.logger.info(f'Zapisano ukupno {row_out} slogova u izlaznu JSON datoteku "{json_out_fn}"')

    tr_count = models.triprecords_count(uf_id)
    app.logger.info(f'Baza sad sadrzi {tr_count} slogova trip recorda')
    return tr_count


def process_hac_workbook(uf_id, wbfile, json_out_fn):
    # returns: number of TripRecords created from HAC Sheet
    tr_count = None

    workbook = xlrd.open_workbook(wbfile)
    worksheet = workbook.sheet_by_index(0)
    header_rownum = hac_sheet_validate(worksheet)
    
    if header_rownum and uf_id:
        tr_count = hac_sheet_process(uf_id, worksheet, header_rownum, json_out_fn)
    
    app.logger.info(f'Odradio process_hac_workbook na "{wbfile}" - rezultat je u "{json_out_fn}"')
    return tr_count
