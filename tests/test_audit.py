import json
import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np
import rasterio
from rasterio.transform import from_origin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_rasters import overlap, validate
from build_site import build

class AuditTests(unittest.TestCase):
    def test_directional_overlap(self):
        a=np.zeros((20,20),bool); b=a.copy()
        a[5,5]=1; a[15,15]=1; b[5,5]=1
        self.assertEqual(overlap(a,b),.5)
        self.assertEqual(overlap(b,a),1.)
    def test_distance_boundary(self):
        a=np.zeros((10,10),bool); b=a.copy()
        a[2,2]=1; b[2,5]=1
        self.assertEqual(overlap(a,b),1.)
        b[:]=False; b[5,5]=1
        self.assertEqual(overlap(a,b),0.)
    def test_empty_not_unique(self):
        with self.assertRaises(ValueError): overlap(np.zeros((2,2),bool),np.zeros((2,2),bool))
    def test_invalid_values_and_grid(self):
        with tempfile.TemporaryDirectory() as d:
            ref=Path(d)/'ref.tif'; p=Path(d)/'pred.tif'
            profile=dict(driver='GTiff',width=3,height=3,count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(0,300,100,100))
            def write(path,a,**extra):
                with rasterio.open(path,'w',**{**profile,**extra}) as ds: ds.write(a,1)
            a=np.zeros((3,3),dtype='float32');write(ref,a);write(p,a)
            self.assertTrue(validate(p,ref)['format_pass'])
            for value in [float('nan'),float('inf'),-0.01,1.01]:
                a[0,0]=value;write(p,a)
                self.assertFalse(validate(p,ref)['format_pass'])
            a[:]=0;write(p,a,transform=from_origin(1,300,100,100))
            self.assertFalse(validate(p,ref)['checks']['transform_match'])
            write(p,a,crs='EPSG:4326')
            self.assertFalse(validate(p,ref)['checks']['crs_match'])
    def test_template_nodata_and_in_footprint_range(self):
        with tempfile.TemporaryDirectory() as d:
            ref=Path(d)/'ref.tif'; pred=Path(d)/'pred.tif'
            profile=dict(driver='GTiff',width=3,height=3,count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(0,300,100,100))
            template=np.zeros((3,3),dtype='float32'); template[0,0]=-9999
            with rasterio.open(ref,'w',**{**profile,'nodata':-9999}) as ds: ds.write(template,1)
            prediction=np.zeros((3,3),dtype='float32'); prediction[0,0]=np.nan
            with rasterio.open(pred,'w',**{**profile,'nodata':float('nan')}) as ds: ds.write(prediction,1)
            self.assertTrue(validate(pred,ref)['format_pass'])
            # A numeric zero outside the footprint is not a null/nodata value.
            prediction[0,0]=0
            with rasterio.open(pred,'w',**profile) as ds: ds.write(prediction,1)
            self.assertFalse(validate(pred,ref)['format_pass'])

    def test_report_fail_closed(self):
        root=Path(__file__).resolve().parents[1]
        j=json.loads((root/'docs/audit.json').read_text())
        self.assertEqual(len(j['rows']),9);self.assertEqual(len(j['pairs']),72)
        self.assertTrue(all(r['max_overlap_3px']>.7 and not r['unique_under_protocol'] for r in j['rows']))
        card=json.loads((root/'docs/run-card.json').read_text())
        self.assertEqual(card['verdict'],'negative');self.assertLessEqual(len(card['submission_note']),140)
        self.assertIsNone(card['raster_sha256'])
        build(check_only=True)
        page=(root/'docs/index.html').read_text()
        self.assertIn('DO NOT SUBMIT',page)
        self.assertNotIn('download=',page)
        for link in ['review.md','hypotheses.md','audit.json','run-card.json','executive-summary.html']:
            self.assertTrue((root/'docs'/link).exists())

if __name__=='__main__': unittest.main()
