# Query the Gallica SRU API to output documents quantities by types of document and source of collections
# Output data as XML and JSON files
# Create a chart (optionnal)
#  - pie if source = full
#  - donut if source /= full

# usage: python3 SRU_types.py [-source] source [-chart]
#  - source: full, gallica, bnf, partners, integrated, harvested (default=full)
#  - chart


from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import json
import argparse
import sys
import numpy as np
from datetime import date
from dicttoxml import dicttoxml
from matplotlib import cm
import os
import time

# importing constants and vars
sys.path.append(os.path.abspath("/Users/bnf/Documents/BnF/Dev/Dataviz/Gallica-médiation des collections/_python_stuff"))
from dataviz import *

##################
# output folder
##################
OUT = "gallica_types_"

##################
result_inner=[]

# time out between calls to the API
timeout=1


parser = argparse.ArgumentParser()
parser.add_argument("-source","-s", default="full", help="Source of collection: "+' '.join(sources_coll))
parser.add_argument("-chart","-c", action="store_true", help="Produce a graph")
parser.add_argument("-format","-f", default="json", help="Data format (json, xml)")
args = parser.parse_args()

# source of collections
src_target = args.source
try:
    src_index = sources_coll.index(src_target)
    source_fr=sources_coll_fr[src_index]
    provenance=queries_coll[src_index]
    print("###################################\n ...processing source: \033[7m", source_fr,"\033[m")
except:
    print("# source argument [-s] must be in: ")
    print (' '.join(sources_coll))
    quit()


# Check whether the specified path exists or not
isExist = os.path.exists(OUT_folder)
if not isExist:
   os.makedirs(OUT_folder)
   print("...Data are outputed in: ",OUT_folder)

# creating the chart legends
subgroup_names_legs=[]
if args.source=='full':
    for t in types:
        subgroup_names_legs.append(t)
else: # we are requesting all + another source
    for t in types:
        subgroup_names_legs.append(t+":autre")
        subgroup_names_legs.append(t+":"+source_fr)

#print(subgroup_names_legs)

# querying all documents
print ("---------\nQuerying the \033[7m complete \033[m digital collection\n")
for t in types_fr:
  if t=="fascicule": # bug Galica : two criteria depending if we're dealing with harvested partners or not
        search = '(dc.type%20all%20%22fascicule%22%20or%20dc.type%20all%20%22periodique%22)'
  else:
        search = '(dc.type%20all%20%22'+t+'%22)'
  query = SRU + search
  print(query)
  time.sleep(timeout)
  try:
      page = requests.get(query) # Getting page HTML through request
      soup = BeautifulSoup(page.content, 'xml') # Parsing content using beautifulsoup
      te=int(soup.find("numberOfRecords").get_text())
      print (" requesting", t,": ",te)
      total += te
      result.append(te)
      searchs.append(search)
  except:
      print("Wow, ", sys.exc_info()[0], " occurred!\n Maybe a API error, try again!")
      sys.exit(-1)

print (" ---------\n SRU query sample:", query)
print (" --------- raw data from the SRU API:\n" , result)

collection['data'] = {}
collection['data']['query'] = {}
collection['data']['query']['sample_url'] = query
collection['data']['query']['date'] = str(date.today())
collection['data']['query']['collection'] = types
collection['data']['query']['collection_fr'] = types_fr
collection['data']['query']['source'] = 'full'
collection['data']['query']['source_fr'] = 'tout'
collection['data']['query']['search'] = searchs
collection['data']['query']['total'] = total
collection['data']['sru'] = result

output_data(args.format,OUT,collection,"full","","")

if src_target != 'full':
    # querying the targeted sub-collection
    collection={}
    searchs=[]
    print ("---------\nNow querying source: \033[7m", src_target,"\033[m\n")
    i=0
    for t in types_fr:
        if t=="fascicule": # bug Galica : two criteria depending if we're dealing with harvested partners or not
            search = '(dc.type%20all%20%22fascicule%22%20or%20dc.type%20all%20%22periodique%22)'+'%20and%20'+ provenance
        else:
            search = '(dc.type%20all%20%22'+t+'%22)'+'%20and%20'+provenance
        query = SRU + search
        print(query)
        time.sleep(timeout)
        try:
            page = requests.get(query) # Getting page HTML through request
            soup = BeautifulSoup(page.content, 'xml') # Parsing content using beautifulsoup
            te=int(soup.find("numberOfRecords").get_text())
            print (" requesting", t,": ",te)
            total_p += te
            # we build the data for the donut inner circle
            result_inner.append(result[i] - te) # all - partners
            result_inner.append(te) # partners
            result_p.append(te) # partners
            sources.append(' ')
            sources.append(("{:.1f}%".format(te/result[i]*100)) if te/result[i] > 0.05 else '')
            searchs.append(search)
            i+=1
        except:
            print("Wow, ", sys.exc_info()[0], " occurred!\n Maybe a API error, try again!")
            sys.exit(-1)

    print (" ---------\n SRU query sample:", query)
    print (" --------- raw data from the SRU API:\n" , result_p)
    collection['data'] = {}
    collection['data']['query'] = {}
    collection['data']['query']['sample_url'] = query
    collection['data']['query']['total_url'] = provenance
    collection['data']['query']['date'] = str(date.today())
    collection['data']['query']['collection'] = types
    collection['data']['query']['collection_fr'] = types_fr
    collection['data']['query']['source'] = args.source
    collection['data']['query']['source_fr'] = source_fr
    collection['data']['query']['search'] = searchs
    collection['data']['query']['total'] = total_p
    collection['data']['sru'] = result_p
    output_data(args.format,OUT,collection,src_target,"","")
    print (" ---------\n total documents:", total_p)

if not(args.chart):
    sys.exit(-1)

# creating a chart
NUM_TYPES = len(types_fr)

fig, ax = plt.subplots()
# color themes: https://matplotlib.org/api/pyplot_summary.html#colors-in-matplotlib
#bmap = plt.colormaps["tab20b"]
bmap = cm.get_cmap('tab20b')
cmap = cm.get_cmap("tab20c")
outer_colors = cmap(np.arange(5)*4)   # 5 color groups in tab20c
bouter_colors = bmap(np.arange(4)*4)  # 4 more color groups
nine_colors = np.concatenate((outer_colors,bouter_colors),axis=0)
cinner_colors = cmap([1, 2, 5, 6, 9, 10, 13, 14, 17, 18])
binner_colors = bmap([1, 2, 5, 6, 9, 10, 13, 14])
inner_colors = np.concatenate((cinner_colors,binner_colors), axis=0)

# outer circle
ax.axis('equal')
mypie, _ = ax.pie(result, radius=1.2,  colors=nine_colors, textprops={'fontsize': 11,'fontweight':'bold'})
plt.setp( mypie, width=0.7, edgecolor='white')

if args.source!='full':
    # Second Ring (inside)
    mypie2, _ = ax.pie(result_inner, radius=1.2-0.3,
    labels=sources, labeldistance=0.7, colors=inner_colors, textprops={'fontsize': 9})
    plt.setp( mypie2, width=0.7, edgecolor='white')
    plt.margins(0,0)

bbox_props = dict(boxstyle="square,pad=0.2", fc="w", ec="k", lw=0.72)
kw = dict(arrowprops=dict(arrowstyle="-"),
          bbox=bbox_props, zorder=0, va="center")

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, subgroup_names_legs, loc='best', fontsize=8)

for i, p in enumerate(mypie):
    ang = (p.theta2 - p.theta1)/2. + p.theta1
    y = np.sin(np.deg2rad(ang))
    x = np.cos(np.deg2rad(ang))
    horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
    connectionstyle = "angle,angleA=0,angleB={}".format(ang)
    kw["arrowprops"].update({"connectionstyle": connectionstyle})
    ax.annotate(types_fr[i]+" : {} ({:.1f}%)".format(result[i], result[i]/total*100), xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                horizontalalignment=horizontalalignment, fontsize=10,**kw)

if args.source!='full':
    plt.title('Gallica - Répartition des types de documents de source \''+source_fr+ "\', total : "+str(total_p)+' ('+"{:.1f}%".format(total_p/total*100)+')\nrelativ. à la collection complète, total : '+str(total)+' - Source : API Gallica SRU')
else:
    plt.title('Gallica - Répartition des types de documents, total : '+str(total)+' - Source : API Gallica SRU')

plt.show()


#colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
#plt.pie(result.values(), labels=types, colors=colors,
#        autopct='%1.1f%%', shadow=True, startangle=90)

#plt.axis('equal')

#plt.show()
