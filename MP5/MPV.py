from labviii import WebScrapper
import re
import shelve
import tkinter as tk
import tkinter.scrolledtext as tkst
import webbrowser

class WebScrapperExtended(WebScrapper):

        

    def parse(self):
        '''Next butonuna basilarak bir sonraki sayfaya (varsa) gidiyoruz
        '''

        for category_name, category_link in self.categories.items():
            print("Performing Category: {} with link {}".format(
                category_name, category_link))
            
            prices = []
            parse_link = category_link

            while (parse_link is not None):
                soup = self.get_soup(category_link)
                # List toplamasi -> [1, 2 ]+ [3, 4] = [1,2,3,4]
                prices += self.get_prices_stars(soup, parse_link)
                parse_link = self.get_next_page(parse_link)
            
            self.prices[category_name] = prices
        
        self.close_db()


    def get_next_page(self, link):
        '''Eger bir next sayfasi varsa o sayfanin tam adresinin dondurur. Yoksa None.
        '''
        soup = self.get_soup(link)
        next_link = soup.find('a', string=re.compile('next'))
        if next_link is None:
            print("Could not find a next page in {}".format(link))
            return None

        # Son kismi degistirmek yeterli
        next_combined_link = re.sub(r'(/)([^/]+.html)', '/'+next_link.get('href'), link)
        print("Found a next page, scraping {}".format(next_combined_link))
        return next_combined_link






class AyiklamaEkrani(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.initGui()
        self.pack()


        self.db_name = 'kitaplar.db'
        self.parse_if_not_parsed()
        
        self.kategoriler = []
        for kategori in self.sozluk.keys():
            self.kategoriler.append(kategori)
            self.fr1_listbox1.insert(tk.END, kategori)




    def parse_if_not_parsed(self):

        try:
            self.sozluk = shelve.open(self.db_name, flag='r')
        except Exception as e:
            print ("Scrapping WebPage since {} file does not exits with error: {}".format(self.db_name, e))
            ws = WebScrapperExtended(self.db_name)
            ws.parse()
            self.sozluk = shelve.open(self.db_name, flag='r')

    def initGui(self):

        self.frame1 = tk.Frame(self)

        self.f1_label1 = tk.Label(self.frame1, text="Kitap Kategorileri")
        self.fr1_listbox1 = tk.Listbox(
            self.frame1, width=40, selectmode="multiple", exportselection=0)

        self.f11_filtre = tk.Button(
            self.frame1, text="Goster", command=self.filtrele)
    
        self.T1 = tkst.ScrolledText(self.frame1, font="Italic 13 bold", width=60, height=20, relief="sunken", bd="5px")
        
        # Bu kismi linklerin sag tiklandiginda acilmasi icin. 
        self.T1.tag_config('link', foreground="blue")
        self.T1.tag_bind('link', '<Button-2>', self.select_event)
        self.T1.insert(tk.END, "Yandaki filtereler ile aramanizi yapip, Goster butonu ile arama yapabilirsiniz. \n\n(Gitmek istediginiz kitap sayfasina arama yaptiktan sonra orta mouse butonu ile giderbilirsiniz...)")

        self.frame2 = tk.Frame(self.frame1, highlightbackground="black" , highlightthickness=1)
        self.fr2_label_min = tk.Label(self.frame2, text="Min Fiyat Secin [0-100]")
        self.fr2_scale_min = tk.Scale(self.frame2, from_=0, to=100, orient=tk.HORIZONTAL, length=160)

        self.fr2_label_max = tk.Label(self.frame2, text="Max Fiyat Secin [0-100]")
        self.fr2_scale_max = tk.Scale(
            self.frame2, from_=0, to=100, orient=tk.HORIZONTAL, length=160)
        self.fr2_scale_max.set(100)



        self.fr2_label_min.pack()
        self.fr2_scale_min.pack()
        self.fr2_label_max.pack()
        self.fr2_scale_max.pack()

        self.frame3 = tk.Frame(self.frame1)
        self.fr2_label_rating = tk.Label(
            self.frame3, text="Rating Secin:")
        options_list = ['Hepsi', '1', '2', '3', '4', '5']
        self.value_inside = tk.StringVar()
        self.value_inside.set("Hepsi")
        self.fr2_option = tk.OptionMenu(
            self.frame3, self.value_inside, *options_list)
        self.fr2_label_rating.pack()
        self.fr2_option.pack()

        self.f1_label1.grid(row=0, column=0)
        self.fr1_listbox1.grid(row=1, column=0)
        self.frame2.grid(row = 2, column = 0)
        self.frame3.grid(row=3, column=0)
        self.f11_filtre.grid(row = 4, column = 0)
        self.T1.grid(row = 0, column = 1, rowspan = 4)

        self.frame1.pack()

    def select_event(self, event):
        ''' Bu kismi linklere tiklandiginda web sayfasi acilsin diye yapildi 
        '''
        webbrowser.open(event.widget.tag_names(tk.CURRENT)
                        [-1])

    def filtrele(self):
        self.T1.delete('1.0', tk.END)
        idxs = self.fr1_listbox1.curselection()
        if (len(idxs)<1):
            # Hic secili olmadigi icin hepsi secili gibi davranacagiz:
            secili_kategoriler = self.kategoriler
        else:
            secili_kategoriler = []
            for idx in idxs:
                secili_kategoriler.append(self.kategoriler[idx])
        
        for kat in secili_kategoriler:
            for deger in self.sozluk[kat]:
                if self.fiyat_filtre(deger) and self.puan_filtre(deger):
                    # En sondaki link ile baslayan tuple, orta mouse butonu ile websayfasina gitmek icin 
                    # Burada tanimlanan `tag_names` ozelligi select_event fonksiyonunda kullaniliyor
                    self.T1.insert(
                        tk.END, deger['Name']+'-> £'+str(deger['Price'])+' -> Rating: ' + str(deger['Rating']) + ''+'\n',  ('link', deger['URL']))

    def fiyat_filtre(self, deger):
        minVal = self.fr2_scale_min.get()
        maxVal = self.fr2_scale_max.get()
        return  minVal < deger['Price'] < maxVal
    
    def puan_filtre(self, deger):
        if 'Hepsi' == self.value_inside.get():
            selected_stars = [1,2,3,4,5]
        else:
            selected_stars = [int(self.value_inside.get())]
        return deger['Rating'] in selected_stars



root = tk.Tk()
root.title("Veri Kazıma ve Filtreleme")
#root.geometry("650x650+400+100")

AyiklamaEkrani(root)
root.mainloop()
