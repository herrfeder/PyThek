import json
from pprint import pprint
from bs4 import BeautifulSoup as bs4
import mechanize

class GenParsing(object):
    def __init__(self):
        self.vidlink=""
        pass

    def parsing(self,url,quality,channel):
        if "zdf" in channel:
            self.vidlink = self.ZDFDRsatXMLparsing(url,str(quality))
        if "ard" in channel:
            self.vidlink = self.ARDJSONparsing(url,str(quality))
        return self.vidlink

    def ZDFDRsatXMLparsing(self,xmlinput,quality):
        qual_dict = {"1":"low","2":"high","3":"very high","4":"hd"}
        br = clickLink(xmlinput,"no")
        xmltext = br.response().read()
        xmltext = bs4(xmltext)
        for entry in xmltext.findAll("formitaet"):


            if qual_dict[quality] in entry.findAll("quality")[0].text:
                if entry.findAll("url")[0].text.endswith("mp4"):
                    temp_url=entry.findAll("url")[0].text
                    if temp_url is not None:
                        return temp_url


    def ARDJSONparsing(self,json_url,quality):

     
        br = prepareBrow()
        response = br.open(json_url)
        json_str = response.read()
        data = json.loads(str(json_str))

        qual_dic={}
        try:
            for i in range(0,10):
                qual_dic[i]=str(data["_mediaArray"][0]["_mediaStreamArray"][i]["_quality"])
        except:
            True

        print qual_dic
        qual_index = qual_dic.keys()[qual_dic.values().index(quality)]

        return str(data["_mediaArray"][0]["_mediaStreamArray"][qual_index]["_stream"])


def clickLink(link,channelStr):

    br = prepareBrow()
    if channelStr!="no":
        url = generateURL(link,channelStr)
    else:
        url = link
    br.open(url)

    return br


def prepareBrow():

        br = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))

        br.set_handle_robots(False)
        br.set_handle_refresh(False)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; de-DE; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.open("http://google.com")
        return br


