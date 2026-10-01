import unittest, collect
class TestExtraction(unittest.TestCase):
 def test_uncertain_dates_are_not_invented(self):
  for v in ['1926?', 'Z', '1930-1935', '1930/02/31', '']:self.assertIsNone(collect.timevalue(v))
 def test_precision(self):
  for v,p in [('1926',9),('1926/08',10),('1926/08/01',11)]:self.assertEqual(collect.timevalue(v)['precision'],p)
 def test_image_only_row_preserved(self):
  p=collect.Parser(True);p.feed('<table id="tablepress-77"><tr><td><img src="https://ephemerajpp.com/wp-content/uploads/test.jpg?w=10"></td></tr></table>')
  self.assertEqual(p.rows[0][0]['images'],['https://ephemerajpp.com/wp-content/uploads/test.jpg'])
 def test_image_origin(self):
  self.assertIsNone(collect.imageurl('https://example.org/test.jpg'))
  self.assertIsNone(collect.imageurl('javascript:alert(1)'))
if __name__=='__main__':unittest.main()
