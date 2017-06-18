# -*- coding: utf-8 -*-
__version__=1.0
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import (ObjectProperty,DictProperty , ListProperty, StringProperty,NumericProperty)
from kivy.factory import Factory
from kivy.uix.carousel import Carousel
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListItemButton
from kivy.uix.selectableview import SelectableView
from kivy.uix.gridlayout import GridLayout
from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.listview import ListView
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior 
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.videoplayer import VideoPlayer
from kivy.graphics import Color
from kivy.uix.progressbar import ProgressBar


import threading
import searchengine
from kivy.clock import Clock
from functools import partial
from kivy.network.urlrequest import UrlRequest
import os
import sys
import pickle
from IPython.core.debugger import Tracer
os.environ['KIVY_VIDEO'] = 'gstplayer'
os.environ['KIVY_AUDIO'] = 'ffpyplayer'


Factory.register('SelectableView', cls=SelectableView)
Factory.register('ListItemButton', cls=ListItemButton)
Factory.register('GridLayout', cls=GridLayout)


Builder.load_string('''

<ThumbnailedGrid@ButtonBehavior+BoxLayout+SelectableView> 
        aa_label: aa_label
        ab_label: ab_label
        ba_label: ba_label
        bb_label: bb_label
        entry_image: entry_image
        canvas.before:
                Color:
                        rgba: .200,.200,.200,1
                Rectangle:
                        pos: self.pos
                        size: self.size
        padding: 3
        index: self.index
        height: self.height
        text: self.text
        GridLayout:
                cols:2
                Image:
                        id: entry_image
                        source: root.thumb
                        height: 30
                        size_hint_x:1

                GridLayout:
                        size_hint_x:2
                        canvas.before:
                                Color:
                                        rgba: .150,.150,.150,1
                                Rectangle:
                                        pos: self.pos
                                        size: self.size
                        cols:2
                        rows:2
                        Label:
                                id: aa_label
                                font_size: 10
                                text: root.entry_name
                        Label:
                                id: ab_label
                                font_size: 10
                                text: root.number

                        Label:
                                id: ba_label
                                font_size: 10
                                text: root.length
                        Label:
                                id: bb_label
                                font_size: 10
                                text: root.date


<DownloadItem@BoxLayout+SelectableView>
        size_hint_y: .2
		download_progress_bar: download_progress_bar
        canvas.before:
                Color:
                        rgba: .200,.200,.200,1
                Rectangle:
                        pos: self.pos
                        size: self.size

        BoxLayout:
                orientation: "horizontal"	
                Image:
                        source: root.thumb
                BoxLayout:
                        padding: 5
                        orientation: "vertical"
                        Label:
                                font_size: 10
                                text: root.name
                        Label: 
                                text: root.length
                                font_size: 10
                        ProgressBar:
                                id: download_progress_bar
                                max: 1
                                value: 0



''')


def load_obj():
    with open('searching_dict.pkl','rb') as f:
        return pickle.load(f)

class WeatherRoot(FloatLayout):
    carousel = ObjectProperty()
    searching = ObjectProperty()
    channels = ObjectProperty()
    storage = ObjectProperty()
    start = ObjectProperty()
    statuslabel = ObjectProperty()

    def __init__(self, **kwargs):
        super(WeatherRoot, self).__init__(**kwargs)
        self.show_searching()
        global root
        global statuslabel
        root = self
        statuslabel = self.statuslabel
        Window.clearcolor = (.240,.240,.240,1)

    def show_start(self):
        self.carousel.load_slide(self.start)
    def show_searching(self):
        self.carousel.load_slide(self.searching)
    def show_channels(self):
        self.carousel.load_slide(self.channels)
    def show_storage(self):
        self.carousel.load_slide(self.storage)

class WeatherApp(App):
    def on_stop(self):
        self.root.stop.set()

class Channels(BoxLayout):
    pass

class DownloadItem(FloatLayout,SelectableView):

    length = StringProperty()
    name = StringProperty()
    link = StringProperty()
    thumb = StringProperty()

    def __init__(self, **kwargs):
        super(DownloadItem, self).__init__(**kwargs)
        self.length = kwargs.get('length','')
        self.name = kwargs.get('name','')
        self.link = kwargs.get('link','')
        self.thumb = kwargs.get('thumb','')


    def remove(self, req, result):
        pass

class Storage(FloatLayout):

    stop = threading.Event()
    download_table = ObjectProperty()
    left_box = ObjectProperty()
    middle_box = ObjectProperty()
    right_box = ObjectProperty()
    def __init__(self, **kwargs):
        super(Storage, self).__init__(**kwargs)
        global storage
        storage = self
        self.download_dict = searchengine.ndict()
        self.download_media_data = searchengine.ndict()
        self.init_adapters()

    def download_content(self,vidlink, broadcast_data, entry_name,element,broadcast_key):
        self.element = element
        statuslabel.text="Downloading: "+element.entry_name[0:10]+"..."
        
        self.add_download( self.element,vidlink)
        self.update_adapters()
        self.update_download_table()

        print "test"
        req = UrlRequest(vidlink, on_progress=self.update_progress, chunk_size=1024, on_success=self.remove_download,file_path="Downloads/"+element.entry_name)
        req.setName(element.entry_name)
        self.store_media_data(broadcast_data, entry_name,broadcast_key)

    def store_media_data(self,broadcast_data,entry_name,broadcast_key):

        self.download_media_data.update(broadcast_data)
        create_broadcast_view(self.download_media_data,self.left_box)
        broadcast_data[broadcast_key]['episodes'][entry_name] = self.download_dict[entry_name]
        Tracer()()
        create_episode_view(self.download_media_data["episodes"][entry_name],self.middle_box)




    def add_download(self,element, vidlink):
        self.download_dict[element.entry_name]["name"] = element.entry_name
        self.download_dict[element.entry_name]["thumb"] = element.thumb
        self.download_dict[element.entry_name]["link"] = vidlink
        self.download_dict[element.entry_name]["length"] = element.length

    def remove_download(self, request, test):
        self.download_dict.pop(request.name,None)
        self.update_adapters()
        self.update_download_table()
 
        self.left_box.add_widget(self.left_box.broadcast_list_view)
        self.middle_box.add_widget(self.middle_box.episodes_list_view)

    def update_progress(self, request, current_size, size):
        self.download_table.download_dict_adapter.selection[0].download_progress_bar.value = current_size / size
        self.update_download_table()
        print current_size
    
    def init_adapters(self):
        self.download_item_args_converter = \
                lambda row_index, rec: {'name': rec['name'],
                                        'thumb': rec['thumb'],
                                        'link': rec['link'],
                                        'length': rec['length'],
                                        'height': 100,
                                        'size_hint_y': 1}
    def update_download_table(self):

        if self.download_table.download_list_view:
            self.download_table.remove_widget(self.download_table.download_list_view)
        self.download_table.add_widget(self.download_table.download_list_view)



    def update_adapters(self):
        categories = sorted(self.download_dict.keys())
        self.download_table.download_dict_adapter = \
                DictAdapter(
                    sorted_keys = categories,
                    data = self.download_dict,
                    args_converter = self.download_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=DownloadItem)

        self.download_table.download_list_view = \
                ListView(adapter=self.download_table.download_dict_adapter,
                         padding=2,
                         size_hint=(1,1))




class Start(BoxLayout):
    pass

class SelectableChannel(BoxLayout):

    def __init__(self, **kwargs):
        super(SelectableChannel, self).__init__(**kwargs)
        self.orientation = "horizontal"
        self.channel_list = kwargs.get("channel_list","")
        self.result_dict = {}
        for text in self.channel_list:
            inner_select = BoxLayout()
            inner_select.orientation = "horizontal"
            inner_select.add_widget(Label(text=text))
            checkbox = CheckBox()
            checkbox.bind(active=self.on_checkbox_active)
            checkbox.id = text
            inner_select.add_widget(checkbox)
            self.add_widget(inner_select)

    def on_checkbox_active(self,checkbox,value):
        if value==True:
            self.result_dict[checkbox.id]=1
        if value==False:
            self.result_dict[checkbox.id]=0




class Searching(BoxLayout):
    #the property "search_input" will be created as an instance of the ObjectProperty class
    search_input = ObjectProperty()
    cascading_view = ObjectProperty()
    channelselect = ObjectProperty()
    # just a normal method, not an event handler
    def __init__(self, **kwargs):
        super(Searching, self).__init__(**kwargs) 
        self.searchOb = searchengine.ThreadedSearch()
        self.searching_media_data = None
        self.broadcast_search_running = False
        self.last_selected = None
        self.vidlink = None

    def broadcast_data_reception(self,dt):

        if self.searchOb.result_dict != None:
            self.searching_media_data = self.searchOb.result_dict
            self.parseBroadcasts()
            Clock.unschedule(self.broadcast_data_reception)
            self.broadcast_search_running = False

    def search_query(self):
        #self.channelselect.add_widget(SelectableChannel(channel_list=["ARD","ZDF","3sat","NDR","MDR","ARTE"]))
        if self.broadcast_search_running == False:
            if DEBUG==0:
                user_query=self.search_input.text
                t = threading.Thread(target=self.searchOb.run, args=("alphabetical",["ard"],".",".",user_query))
                t.start()
                Clock.schedule_interval(self.broadcast_data_reception,0.5)
                self.broadcast_search_running = True
            else:
                self.searching_media_data = load_obj()
                self.parseBroadcasts()
        else:
            print("Search is already running")
  
    def parseBroadcasts(self):

        self.cascView =CascadingView(broadcasts=self.searching_media_data)
        
        self.cascView.drawBroadcasts(self.searching_media_data)
        self.cascView.left_box.broadcast_list_view.bind(
            on_touch_down=self.create_broadcast_clock,
            on_touch_up=self.delete_broadcast_clock)


        self.add_widget(self.cascView)
        self.cascView.pos = 0,0
        self.cascView.left_box.broadcast_dict_adapter.bind(on_selection_change=self.parseEpisodes)

    def create_broadcast_clock(self,widget,touch, *args):
        if self.cascView.left_box.broadcast_list_view.collide_point(touch.pos[0],touch.pos[1]):
            callback = partial(self.add_favorites, touch, widget)
            Clock.schedule_once(callback,2)
            self.broadcasttouch = touch
            self.broadcasttouch.ud['event'] = callback 

    def delete_broadcast_clock(self,widget,touch, *args):

        if self.cascView.left_box.broadcast_list_view.collide_point(touch.pos[0],touch.pos[1]):
            Clock.unschedule(self.broadcasttouch.ud['event'])

    def add_favorites(self, touch, widget, *args):
        print dir(widget)
        Tracer()()
        print "add favorites"

    def parseEpisodes(self,instance):
        if self.last_selected != None:
            self.last_selected.unmark_choosen() 
        instance.selection[0].mark_choosen()
        self.last_selected = instance.selection[0]


        broadcast_temp = instance.selection[0]
        if DEBUG==0: 
            t = threading.Thread(target=self.searchOb.run, args=("episodes",[broadcast_temp.channel],broadcast_temp.url,broadcast_temp.entry_name))
            t.start()
            t.join()
            self.searching_media_data=self.searchOb.result_dict
        with open('./download_dict.pkl','wb') as f:
            pickle.dump(self.searching_media_data, f, pickle.HIGHEST_PROTOCOL)

        self.cascView.drawEpisodes(self.searching_media_data[broadcast_temp.entry_name]["episodes"])
        self.cascView.middle_box.episodes_list_view.bind(
            on_touch_down=self.create_episode_clock,
            on_touch_up = self.delete_episode_clock)

        #self.cascView.episodes_list_adapter.bind(on_selection_change=self.showVideo)

    def create_episode_clock(self,widget,touch, *args):

        if self.cascView.middle_box.episodes_list_view.collide_point(touch.pos[0],touch.pos[1]):
            callback = partial(self.menu, touch, widget)
            Clock.schedule_once(callback,0.2)
            self.episodetouch = touch
            self.episodetouch.ud['event'] = callback

    def delete_episode_clock(self, widget, touch, *args):

        if self.cascView.middle_box.episodes_list_view.collide_point(touch.pos[0],touch.pos[1]):
            Clock.unschedule(self.episodetouch.ud['event'])

    def menu(self, touch, widget, *args):
        menu = BoxLayout(size_hint=(None, None),
                         orientation='vertical',
                         center=touch.pos)
        sync = Button(text="Sync")
        sync.bind(on_release=partial(self.syncing_file,widget))
        play = Button(text="Play")
        play.bind(on_release=partial(self.showVideo,widget))
        menu.add_widget(sync)
        menu.add_widget(play)
        close = Button(text='close')
        close.bind(on_release=partial(self.close_menu, menu))
        menu.add_widget(close)
        root.add_widget(menu)
    def close_menu(self, widget, *args):
        root.remove_widget(widget)

    def syncing_file(self, episode_element, *args):
        self.temp_element = episode_element.adapter.selection[0]
        self.extractvid(self.temp_element.channel, self.temp_element.url)
        self.command = "sync"

    def trigger_sync(self):
        broadcast_key = self.searching_media_data.findkey(self.temp_element.entry_name,self.searching_media_data)[0]
        temp_data = searchengine.ndict()
        temp_data[broadcast_key] = self.searching_media_data[broadcast_key]
        storage.download_content(self.vidlink,temp_data,self.temp_element.entry_name,self.temp_element,broadcast_key)


    def extractvid(self,channel,url):

            self.vidlink_search_running = True
            t = threading.Thread(target=self.searchOb.run, args=("generate",[channel],url))
            t.start()
            Clock.schedule_interval(self.vidlink_reception,0.5)
    def vidlink_reception(self,dt):

        
        if self.searchOb.vidlink != None:
            self.vidlink = self.searchOb.vidlink
            self.vidlink_search_running = False
            if "sync" in self.command:
                self.trigger_sync()
            Clock.unschedule(self.vidlink_reception)

    def showVideo(self,instance, *args):

        try:
            episode_temp = instance.selection[0]
        except:
            episode_temp = instance.adapter.selection[0]
        url = episode_temp.url

        self.extractvid(episode_temp.channel,url)

        self.cascView.drawVideo(self.vidLink)


class ScrollChannels(BoxLayout):
    source = StringProperty()

    def set_channel(self):
        pass


class ThumbnailedGrid(ButtonBehavior,BoxLayout,SelectableView):

    entry_name = StringProperty()
    description = StringProperty()
    thumb = StringProperty()
    number= StringProperty()
    length = StringProperty()
    date = StringProperty()
    channel = StringProperty()
    aa_label = ObjectProperty()
    ab_label = ObjectProperty()
    entry_image = ObjectProperty()


    def __init__(self,**kwargs):
        super(ThumbnailedGrid, self).__init__(**kwargs)
        self.entry_name=kwargs.get('text','')
        self.thumb=kwargs.get('thumb','')
        self.number=kwargs.get('number','')
        self.url=kwargs.get('url','')
        self.channel = kwargs.get('channel','')
        self.length = ""
        self.date = ""
        self.aa_label.color = [0,0,0,1]
        self.ab_label.color = [0,0,0,1]
        self.opacity = .75

    def mark_choosen(self):
        self.opacity = 1
        self.entry_image.size_hint_x = 2

    def unmark_choosen(self):
        self.opacity = .75
        self.entry_image.size_hint_x = 1


def create_broadcast_view(media_data, objref):
    objref.broadcast_item_args_converter = \
            lambda row_index, rec: {'text': rec['name'],
                                    'thumb':rec['thumb'][1],
                                    'number':rec['number'],
                                    'channel':rec['channel'],
                                    'url':rec['url'],
                                    'size_hint_y': 8,
                                    'height': 80,
                                    'width': 100}

    categories = sorted(media_data.keys())
    objref.broadcast_dict_adapter = \
            DictAdapter(
                sorted_keys = categories,
                data = media_data,
                args_converter = objref.broadcast_item_args_converter,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ThumbnailedGrid)

    objref.broadcast_list_view = \
            ListView(adapter=objref.broadcast_dict_adapter,
                     padding=2,
                     size_hint=(.4, 1.0))

def create_episode_view(media_data, objref):
    objref.episode_item_args_converter = \
                    lambda row_index, rec: {'name': rec['name'],
                                            'url': rec['url'],
                                            'thumb': rec['thumb'][1],
                                            'length': rec['length'],
                                            'number': rec['number'],
                                            'channel': rec['channel'],
                                            'size_hint_y': 5,
                                            'height': 80,
                                            'width': 100}

    categories = sorted(media_data.keys())
    objref.episodes_list_adapter = \
        DictAdapter(
            sorted_keys=categories,
            data=media_data,
            args_converter=objref.episode_item_args_converter,
            selection_mode='single',
            allow_empty_selection=False,
            cls=ThumbnailedGridEpisode)



    objref.episodes_list_view = \
       ListView(adapter=objref.episodes_list_adapter,
                padding=2,
                size_hint=(.4,1.0))
      

class ThumbnailedGridEpisode(ThumbnailedGrid):


    def __init__(self,**kwargs):
        super(ThumbnailedGrid, self).__init__(**kwargs)
        self.entry_name = kwargs.get('name','')
        self.length = kwargs.get('length','')
        self.date = kwargs.get('date','')
        self.url = kwargs.get('url','')
        self.number = ""
    def do_test(self,index):
        print "EpisodeIndex:"+str(index)



class CascadingView(AnchorLayout):

    left_box = ObjectProperty()
    middle_box = ObjectProperty()
    right_box = ObjectProperty()
    def __init__(self, **kwargs):
        self.broadcasts = kwargs.get("broadcasts","")
        self.padding = [10, 30, 10, 40 ]
        super(CascadingView, self).__init__(**kwargs)



    def drawBroadcasts(self,media_data):
        try:
            if self.left_box.broadcast_list_view:
                self.left_box.remove_widget(self.left_box.broadcast_list_view)
        except:
        

            create_broadcast_view(media_data,self.left_box)
            self.left_box.add_widget(self.left_box.broadcast_list_view)


    def drawEpisodes(self,media_data):
        try:
            if self.middle_box.episodes_list_view:
                print "doubletime"
                self.middle_box.remove_widget(self.middle_box.episodes_list_view)
        except:
            pass
        create_episode_view(media_data,self.middle_box)
        self.middle_box.add_widget(self.middle_box.episodes_list_view)

    def drawVideo(self,url):
        try:
            if self.right_box.player:
                self.right_box.player.state = 'stop'
                self.right_box.remove_widget(self.right_box.player)
        except:
            pass
        self.right_box.player = PyThekVideoPlayer(source=url, state='play',options={'allow_stretch':True})

        self.right_box.add_widget(self.right_box.player)



class PyThekVideoPlayer(BoxLayout):

    url = StringProperty()
    state = StringProperty()
    options = DictProperty()
    pyplayer = ObjectProperty()

    def __init__(self,**kwargs):
        self.url = kwargs.get("source")
        self.state = kwargs.get("state")
        self.options = kwargs.get("options")
        super(PyThekVideoPlayer, self).__init__(**kwargs)
 
    def player_resize(self):
        self.pyplayer.fullscreen == True


if __name__ == '__main__':
    global DEBUG
    DEBUG = 1
    WeatherApp().run()


