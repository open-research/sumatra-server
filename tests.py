
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import Client
try:
    import json
except ImportError:
    import simplejson as json
import base64
#from pprint import pprint

def deunicode(D):
    """Convert unicode keys and values to str"""
    E = {}
    for k,v in D.items():
        if isinstance(v, dict):
            v = deunicode(v)
        elif isinstance(v, unicode):
            v = str(v)
        elif isinstance(v, list):
            v = [deunicode(d) for d in v]
        E[str(k)] = v
    return E

class BaseTestCase(TestCase):
    fixtures = ['haggling', 'permissions']

    def setUp(self):
        # thanks to Thomas Pelletier for this function
        # http://thomas.pelletier.im/2009/12/test-your-django-piston-api-with-auth/
        self.client = Client()
        auth = '%s:%s' % ('testuser', 'abc123')
        auth = 'Basic %s' % base64.encodestring(auth)
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
        }

    def assertMimeType(self, response, desired_mimetype):
        mimetype, charset = response["Content-Type"].split(";")
        self.assertEqual(mimetype, desired_mimetype)


class ProjectListHandlerTest(BaseTestCase):    
    
    def setUp(self):
        self.client.login(username="testuser", password="abc123")
    
    def test_GET_no_data(self):
        prj_list_uri = reverse("sumatra-project-list")
        response = self.client.get(prj_list_uri)
        self.failUnlessEqual(response.status_code, 200)
        self.assertMimeType(response, "application/json")
        data = json.loads(response.content)
        assert isinstance(data, list)
        self.assertEqual(len(data), 1)
        prj = data[0]
        self.assertEqual(prj["uri"], "http://testserver%sTestProject/" % prj_list_uri)
        
    def test_GET_format_html(self):
        prj_list_uri = reverse("sumatra-project-list")
        response = self.client.get(prj_list_uri, {"format": "html"})
        self.failUnlessEqual(response.status_code, 200)
        self.assertMimeType(response, "text/html")
        
        
class ProjectHandlerTest(BaseTestCase):
    
    #def setUp(self):
    #    self.client.login(username="testuser", password="abc123")
        
    def test_GET_no_data(self):
        prj_uri = reverse("sumatra-project",
                          kwargs={"project": "TestProject"})
        response = self.client.get(prj_uri, {}, **self.extra)
        #print response.content
        self.assertEqual(response.status_code, 200)
        self.assertMimeType(response, "application/json")
        data = json.loads(response.content)
        assert isinstance(data, dict)
        self.assertEqual(data["id"], "TestProject")
        assert "testuser" in data["access"]
        assert isinstance(data["records"], list)
        for record in data["records"]:
            touch = self.client.get(record, {}, **self.extra) # should perhaps add support for HEAD to the server
            self.assertEqual(touch.status_code, 200)
        
        
class RecordHandlerTest(BaseTestCase):
    
    def test_GET_no_data(self):
        #label =  "20100709-154255"
        label = "haggling"
        rec_uri = reverse("sumatra-record",
                          kwargs={"project": "TestProject",
                                  "label": label})
        response = self.client.get(rec_uri, {}, **self.extra)
        #print response.content
        self.assertEqual(response.status_code, 200)
        self.assertMimeType(response, "application/json")
        data = json.loads(response.content)
        assert isinstance(data, dict)
        self.assertEqual(data["label"], label)
        self.assertEqual(set(data.keys()),
                         set(("executable","label","reason",
                              "duration","executable","repository",
                              "main_file","version","parameters",
                              "launch_mode","datastore","outcome",
                              "data_key","timestamp","tags","diff",
                              "user","dependencies", "platforms")))
        self.assertEqual(data["tags"], "foobar")
        
        
    def test_GET_format_html(self):
        label = "haggling"
        rec_uri = reverse("sumatra-record",
                          kwargs={"project": "TestProject",
                                  "label": label})
        response = self.client.get(rec_uri, {"format": "html"}, **self.extra)
        self.failUnlessEqual(response.status_code, 200)
        self.assertMimeType(response, "text/html")
        
        
    def test_PUT_new_record_json(self):
        new_record = {
            "label": "abcdef",
            "reason": "uygnougy",
            "duration": 32.1,
            "executable": {
                "path": "lgljgkjhk",
                "version": "iugnogn",
                "name": "kljhnhn",
             },
            "repository": {
                "url": "iuhnhc;<s",
                "type": "iufvbfgbjlml",
            },
            "main_file": "OIYUGUIYFU",
            "version": "LUGNYGNYGu",
            "parameters": {
                "content": "oignuguygnug",
                "type": "hjgjgn65878",
            },
            "launch_mode": {
                "type": "OIUNIU6nkjgbun", 
                "parameters": "GUNYGU76565",
            },
            "datastore": {
                "type": "mosigcqpoejf;",
                "parameters": "oscih,spoirghosgc",
            },
            "outcome": "mihiuhpoip",
            "data_key": "iugbufuyfiutyfitfy",
            "timestamp": "2010-07-11 22:50:00",
            "tags": "abcd,efgh,ijklm",
            "diff": "iugoiug,ihg",
            "user": "gnugynygy",
            "dependencies": [{
                "path": "moh,oh",
                "version": "liuhiuhiu",
                "name": "mohuuyfbn",
                "module": "ouitfvbtfky",
                "diff": "liugnig,lug",
                }],
            "platforms": [{
                "system_name": "liugiuyhiuyg", 
                "ip_addr": "igng,iihih,i", 
                "architecture_bits": "vmsilughcqioej;", 
                "machine": "cligcnquefgx", 
                "architecture_linkage": "uygbytfkg", 
                "version": "luyhtdkguhl,h", 
                "release": "lufuytdydy", 
                "network_name": "ouifbf67", 
                "processor": "iugonuyginugugu"
            }],
        }
        prj_uri = reverse("sumatra-project",
                          kwargs={"project": "TestProject"})
        rec_uri = "%s%s/" % (prj_uri, new_record["label"])
        response = self.client.put(rec_uri, data=json.dumps(new_record),
                                   content_type="application/json",**self.extra)
        print response.content
        self.assertEqual(response.status_code, 201)
        
        response = self.client.get(rec_uri, {}, **self.extra)
        self.assertEqual(response.status_code, 200)
        #pprint(deunicode(json.loads(response.content)))
        self.assertEqual(new_record, deunicode(json.loads(response.content)))