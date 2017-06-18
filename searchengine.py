# -*- coding: utf-8 -*-
import mechanize
import re
from bs4 import BeautifulSoup as bs4
import time
import urlparse
import genparsing
from urllib import urlretrieve
import Queue
import threading
import time
import os


class ndict(dict):
    def __missing__(self,key):
        result = self[key] = ndict()
        return result

    def findkey(self,value,dictelement):
        for k,v in dictelement.items():
            if isinstance(v, dict):
                p = self.findkey(value,v)
                if p:
                    return [k] + p
            elif v == value:
                return [k]

class ChannelDict(object):
    def __init__(self):
        self.__channeldict=zip(0, mediathek_dict.keys())
 
    @property
    def channeldict(self):
        return self.channeldict

    def returnactivated(self):
        activ_list=[]
        for key in self.__channeldict:
            if self.__channeldict==1:
                activ_list.append(key)

        return activ_list

    def activateChannel(self,channel):
        try: 
            self.__channeldict[channel]=1
        except:
            print "That channel doesn't exist"
    def resetChannel(self,channel):
        try:
            self.__channeldict[channel]=0
        except:
            print "That channel doesn't exist"
    def resetAll(self,channel):
        self.__channeldict=zip(0,mediathek_dict.keys())



mediathek_dict =\
{"ARD":"http://www.ardmediathek.de/tv",
 "ZDF":"http://www.zdf.de/ZDFmediathek/hauptnavigation/startseite?flash=off",
 "ARTE":"http://www.arte.tv/guide/de/plus7/",
 "NDR":"https://www.ndr.de/mediathek/",
 "3sat":"https://www.3sat.de/mediathek/"}
###################  ARD  #####################
ard_alpha_url = "/sendungen-a-z?sendungsTyp=sendung&buchstabe="
###############################################

################## ZDF ########################
zdf_alpha_url = "/sendung-a-bis-z/saz"
#insert number between 0-8


################## 3sat ########################
DRsat_alpha_url = "?mode=sendungenaz"
#append number between 0-1

DRsat_xml_url = "xmlservice/web/beitragsDetails?id="
############################################################################

class ThreadedSearch(object):
    def __init__(self):

        self.searchen=PythekSearchEngine()
        self.vidlink = ""

        if not os.path.exists("dynamic_pics"):
            os.mkdir("dynamic_pics")

    def run(self, command, channels, url=".", parent_key=".", search_query=".", filters="."):
        self.result_dict = None
        self.vidlink = None
        if "generate" in command:
            for channel in channels:
                t = threading.Thread(target=self.searchen.generateVidLink, args=(url,channel))
                t.start()
                t.join()
            print "VideoLink: "+self.searchen.vidlink
            self.vidlink=self.searchen.vidlink
        if "alphabetical" in command:
            threads=[]
            self.searchen.init_search_data()
            for channel in channels:
                print "starting thread for "+channel
                t = threading.Thread(target=self.searchen.searchAlphabetical, args=(channel,search_query))
                t.start()
                threads.append(t)
                
            for t in threads:
                t.join()
            self.result_dict = self.searchen.search_dict

        if "episodes" in command:
            for channel in channels:
                print "starting episode search thread for "+channel
                t = threading.Thread(target=self.searchen.searchEpisodes, args=(parent_key,url,channel))
                t.start()
                t.join()
            self.result_dict = self.searchen.search_dict

   

class PythekSearchEngine(object):

    def __init__(self):
        self.__result_dict = ndict()
        #self.__ch_dict = ChannelDict()
        self.parsing = genparsing.GenParsing()
        self.vidlink = ""
###############################################################################

    def init_search_data(self):
        self.search_dict = ndict()

    def searchAlphabetical(self,channel,search_query):

        if "zdf" in channel:
            self.search_dict.update(self.ZDFsearch("alphabetical","",search_query))
        if "ard" in channel:
            self.search_dict.update(self.ARDsearch("alphabetical","",search_query))
        if "drsat" in channel:
            self.search_dict.update(self.DRsatsearch("alphabetical","",search_query)) 
        if "ndr" in channel:
            self.search_dict.update(self.ARDsearch("alphabetical","",search_query))
 
        return self.search_dict

    def searchEpisodes(self,parent_key,url,channel):
        if "zdf" in channel:
            self.search_dict[parent_key]["episodes"]=self.ZDFsearch("episodes",url)
        if "ard" in channel:
            self.search_dict[parent_key]["episodes"]=self.ARDsearch("episodes",url)
        if "drsat" in channel:
            self.search_dict.update(self.DRsatsearch("episodes",url)) 
        if "ndr" in channel:
            self.search_dict.update(self.ARDsearch("episodes",url))
        return self.search_dict


    def generateVidLink(self,url,channel): 
        self.vidlink = self.parsing.parsing(url,2,channel)
        return self.vidlink

    def ARDThreadedRange(self,range_list,search_type,url=".",search_query="."):
        result_list = ndict()
        threads = []
        for url_item in range_list:
            print "starting episode thread for ard"
            t = threading.Thread(target=self.ARDSearchAndParse, args=(["url","thumb","number","name"],url_item,search_query))
            t.start()
            threads.append(t)
                
            for t in threads:
                t.join()
            result_list.update(self.ard_list)
        return result_list




    def ARDsearch(self,searchtype,url=".",search_query="."):

        #ard_list= ndict()
        temp_list = []
        letter_list = []
        ard_base_url = mediathek_dict["ARD"]

        if "alphabetical" in searchtype:
            self.ard_list= ndict()
            for i in range(65,65+26):
                letter_list.append(ard_base_url+ard_alpha_url+chr(i))
            letter_list.append(ard_base_url+ard_alpha_url+"0-9")

            return self.ARDThreadedRange(letter_list,"alphabetical",".",search_query)

        if "episodes" in searchtype:
             
            self.ARDSearchAndParse(['url','thumb','length','date','number','name','broadcast'],url)

            return self.ard_list

    def ARDSearchAndParse(self, arguments, url,search_query="."):

        self.ard_list = ndict()
        ard_base_url = mediathek_dict["ARD"]
        br = clickLink(url,"no") 
        html = bs4(br.response().read(),"lxml")
        user_query=re.compile(search_query.lower())
        templink=""

        if search_query==".":
            broadcast_list = html.findAll('div',{"data-ctrl-contentsoptionallayouter-entry":"{}"})
        else:
            broadcast_list = html.findAll('div',{"data-ctrl-sendungenabiszmodminioptionallayouter-entry":"{}"})

        for item in broadcast_list:
            if (user_query.search(item.find("h4").text.lower())):
                entrykey = item.find("h4").text.encode("utf8")
                #print entrykey
                parsed = urlparse.urlparse(item.find("a",{"class":"mediaLink"})["href"])
                recdocumentID = urlparse.parse_qs(parsed.query)['documentId'][0]

                arg_len = len(arguments)
                for i in range(0,arg_len):
                    if arguments[i]=="url":
                        if search_query==".":
                            self.ard_list[entrykey][arguments[i]]= 'http://www.ardmediathek.de/play/media/'+recdocumentID+'?devicetype=pc&features=flash'
                        else: 
                            self.ard_list[entrykey][arguments[i]]='http://www.ardmediathek.de'+item.find("a",{"class":"mediaLink"})["href"]
                    if arguments[i]=="thumb":
                        temp_item=item.find("img",{"class":"img hideOnNoScript"})["data-ctrl-image"]
                        temp_item=temp_item.split("':'")[2].split("'}")[0].replace("##width##","200")
                        temp_thumb="http://www.ardmediathek.de"+temp_item
                        urlretrieve(temp_thumb,"dynamic_pics/ard"+recdocumentID+".jpeg")
                        self.ard_list[entrykey][arguments[i]]=[temp_thumb,"dynamic_pics/ard"+recdocumentID+".jpeg"]
                    if arguments[i]=="number":
                        self.ard_list[entrykey][arguments[i]]=item.find("p",{"class":"dachzeile"}).text.encode("utf8")
                    if arguments[i]=="length":
                        self.ard_list[entrykey][arguments[i]]=item.find("p",{"class":"subtitle"}).text.encode("utf8")
                    if arguments[i]=="date":
                        self.ard_list[entrykey][arguments[i]]=item.find("p",{"class":"dachzeile"}).text.encode("utf8")
                    if arguments[i]=="broadcast":
                        self.ard_list[entrykey][arguments[i]]=html.find('h4',{"class":"headline"}).text.encode("utf8") 
                    if arguments[i]=="additional": 
                        try:
                            desc_list = html.findAll('div',{"class":"FloatText mediathek_float_da_box_mediathek_ListBoxText"})
                            for item in desc_list:
                                if recDocumentID in item.a["href"]:
                                    self.ard_list[entrykey][arguments[i]]= item.find("b")
                        except Exception as e:
                            print e
                    if arguments[i]=="name":
                        self.ard_list[entrykey][arguments[i]]=entrykey

                    self.ard_list[entrykey]["channel"]="ard"
        return self.ard_list


    #######################################################################



    def DRsatSearch(searchtype,url=".",search_query="."):

        DRsat_list = ndict()
        DRsat_base_url = mediathek_dict["3sat"]

        if "alphabetical" in searchtype:
            for i in range(0,2):
                index_url = DRsat_base_url+DRsat_alpha_url+str(i)
                br = clickLink(index_url,"no")

                temp_list = DRsatSearchAndParse(['url','thumb'],br,search_query)

            DRsat_list.update(temp_list) 

            return DRsat_list

        if "episodes" in searchtype:
            
            br = clickLink(url,"no")
            temp_list = DRsatSearchAndParse(['url','thumb','length','additional'],br)

            DRsat_list.update(temp_list)
            return DRsat_list


    def DRsatSearchAndParse(arguments,br,search_query="."):

        DRsat_base_url = mediathek_dict["3sat"]
        DRsat_list = ndict()
        html = bs4(br.response().read(),"lxml")
        documentID=re.compile('obj=[0-9]{3,8}')
        user_query=re.compile(search_query)
        broadcast_query=re.compile('\?red=[0-9a-zA-Z]{1,20}')
        templink=""


        broadcast_list = html.findAll('div',{"class":"BoxPicture MediathekListPic"})
        for item in broadcast_list:
            if (user_query.search(item.a["title"])):
                entrykey = item.img["alt"]
                arg_len = len(arguments)
                for i in range(0,arg_len):
                    if arguments[i]=="url":
                        if search_query==".":
                            recdocumentID=documentID.search(item.a["href"]).group().replace("obj=","")
                            DRsat_list[entrykey][arguments[i]]=DRsat_base_url+DRsat_xml_url+recdocumentID
                        else:    
                            DRsat_list[entrykey][arguments[i]]=item.a["href"]
                    if arguments[i]=="thumb":
                        temp_item=item.img["src"]
                        temp_thumb="http://www.3sat.de"+temp_item
                        urlretrieve(temp_thumb,"dynamic_pics/drsat"+recdocumentID+".jpeg")
                        DRsat_list[entrykey][arguments[i]]=[temp_thumb,"dynamic_pics/drsat"+recdocumentID+".jpeg"]

                    if arguments[i]=="length":
                        DRsat_list[entrykey][arguments[i]]=item.span.text
                    if arguments[i]=="additional": 
                        try:
                            desc_list = html.findAll('div',{"class":"FloatText mediathek_float_da_box_mediathek_ListBoxText"})
                            for item in desc_list:
                                if recDocumentID in item.a["href"]:
                                    DRsat_list[entrykey][arguments[i]]= item.find("b")
                        except Exception as e:
                            print e
                    else:
                        DRsat_list[entrykey][arguments[i]] = ""
        return DRsat_list


    #########################################################################

    def ZDFsearch(self,searchtype,url=".",search_query="."):

        self.zdf_list = ndict()
        zdf_base_url = mediathek_dict["ZDF"]

        if "alphabetical" in searchtype:
            for i in range(0,9):
                index_urlpart = zdf_alpha_url+str(i)
                zdf_index_url=zdf_base_url.replace("startseite",index_urlpart)
                br = clickLink(zdf_index_url,"no") 
                #first of four links includes the image for the broadcast
                #every entry provide four links, we only want the third one
                #which stores the description of the broadcast
                temp_list = self.ZDFsearchAndParse(['url','thumb','sparte','number','name','channel'],br,search_query)
                self.zdf_list.update(temp_list)
        if "episodes" in searchtype:
            
            br = clickLink(url,"no")
            self.zdf_list = self.ZDFsearchAndParse(['url','thumb','number','length','name','channel'],br)

        return self.zdf_list

    def ZDFsearchAndParse(self,arguments,br,search_query="."):
        
        zdf_base_url = mediathek_dict["ZDF"]
        zdf_list = ndict()
        templink="" 
        html=bs4(br.response().read(),"lxml")
        documentID=re.compile('\/[0-9]{3,9}')
        user_query=re.compile(search_query.lower())

        for link in br.links():
            if templink==link.url:
                continue
            templink=link.url
            try:
                recdocumentID = documentID.search(link.url).group().replace("/","")
                recentlinks=html.findAll('a',href=re.compile(recdocumentID))
                if user_query.search(recentlinks[2].text.lower()):
                    entrykey = str(recentlinks[2].text.encode("utf8")).replace("-"," ").replace("ü","ue")
                    #entrykey = "test"
                    #print entrykey
                    arg_len = len(arguments)
                    for i in range(0,arg_len):
                        if arguments[i]=="url":
                            if search_query==".":
                                parturl = "/ZDFmediathek/xmlservice/web/beitragsDetails?id="+recdocumentID
                                entryurl = zdf_base_url.replace("/ZDFmediathek/hauptnavigation/startseite?flash=off",parturl)
                                zdf_list[entrykey][arguments[i]]=entryurl.replace('\xc2\xad', '')

                            else:

                                parturl = recentlinks[2]["href"]
                                entryurl = zdf_base_url.replace("/ZDFmediathek/hauptnavigation/startseite?flash=off",parturl)
                                zdf_list[entrykey][arguments[i]]=entryurl.replace('\xc2\xad', '')
                        if arguments[i]=="thumb":
                            partthumb = recentlinks[0].img["src"]
                            entrythumb =zdf_base_url.replace("/ZDFmediathek/hauptnavigation/startseite?flash=off",partthumb).replace('\xc2\xad', '')
                            if entrythumb:
                                urlretrieve(entrythumb,"dynamic_pics/zdf"+recdocumentID+".jpeg")
                                zdf_list[entrykey][arguments[i]]=[entrythumb,"dynamic_pics/zdf"+recdocumentID+".jpeg"]
                        if arguments[i]=="sparte":
                            entrysparte = recentlinks[1].text
                            #entrysparte = "test"
                            zdf_list[entrykey][arguments[i]]=str(entrysparte)
                        if arguments[i]=="number": 
                            entrynumber = recentlinks[3].text.replace("Ä","AE")
                            #entrynumber = "test"
                            zdf_list[entrykey][arguments[i]]=entrynumber
                        if arguments[i]=="name":
                            zdf_list[entrykey][arguments[i]]=entrykey
                        if arguments[i]=="length":
                            zdf_list[entrykey][arguments[i]]=str(recentlinks[1].text.encode("utf8"))

                        zdf_list[entrykey]["channel"]="zdf"
            except Exception as e:
                print e
            print zdf_list
        return zdf_list



##### MECHANIZE UTILITY #####

def clickLink(link,channelStr,br=None):

    if br==None:
        br = prepareBrow()
    if channelStr!="no":
        url = generateURL(link,channelStr)
    else:
        url = link
    br.open(url)

    return br

def generateURL(link,channelStr):

    url =""

    if channelStr == "ARD":
        url = mediathek_dict["ARD"]  + link[3:]
    elif channelStr == "ZDF" and link=="":
        url = mediathek_dict["ZDF"]

    return url

def prepareBrow():

        br = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))
        br.set_handle_robots(False)
        br.set_handle_refresh(False)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; de-DE; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.open("http://google.com")
        return br


if __name__=='__main__':
    searchob = ThreadedSearch() 
    
    result_dict=searchob.run("alphabetical",["ard","zdf"], url=".", parent_key=".", search_query="test", filters=".") 
    print result_dict
    result_dict=searchob.run("episodes",["ard"], url=result_dict[result_dict.keys()[0]]["url"], parent_key=result_dict.keys()[0])
    print result_dict
    #searchobject = PythekSearchEngine()
    #test_query= raw_input("What looking for?\n")
    #data_dict=searchobject.ARDsearch("alphabetical","",test_query)
    #print data_dict 
    #data_dict= searchobject.ARDsearch("episodes",data_dict[data_dict.keys()[0]]['url'])
    #print ""
    #print ""
    #print data_dict 
    #vid_link = genparsing.ARDJSONparsing(data_dict[data_dict.keys()[1]]['url'],"2")
    #print vid_link
