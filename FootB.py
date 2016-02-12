from bs4 import BeautifulSoup
import urllib2
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import *
import numpy as np
import httplib2

# Define years
y1 = ['{}-{}'.format(i,i+1-1900) for i in range(1929,1999)]
y2 = ['1999-2000']
y3 = ['{}-{:02d}'.format(i,i+1-2000) for i in range(2000,2014)]
years = np.concatenate([y1,y2,y3])

list_La_Liga = ['https://en.wikipedia.org/wiki/{}_La_Liga'.format(y) for y in years]
list_Serie_A = ['https://en.wikipedia.org/wiki/{}_Serie_A'.format(y) for y in years]
list_Serie_A.remove('https://en.wikipedia.org/wiki/2005-06_Serie_A')  #Removed because of Calciopoli scandal

final_list = np.concatenate((list_La_Liga,list_Serie_A))

header = {'User-Agent': 'Mozilla/5.0'} # Needed to prevent 403 error on Wikipedia

def league_name(wpage):
	a = wpage.split('_')[1:][0]
	b = wpage.split('_')[1:][1]
	return a + ' ' + b

def FootB(wpage, league_name):

	req = urllib2.Request(wpage, headers = header)
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page, 'html5lib')	

	all_tables = soup.find_all("table")
	theone = [u'W', u'D','L']
	
	for j in range(0,len(all_tables)):
		rows = all_tables[j].find_all("tr")
		lencols = len(rows[0].find_all("th")) 
		cols = [rows[0].find_all("th")[i].get_text().encode('ascii', 'ignore') for i in range(0, lencols)]
		if (theone[0] in cols) & (theone[1] in cols):
			lenrows = len(rows) - 1
			break

	columns = pd.Series(cols)
	columns[columns == 'Club'] = 'Team'	
	columns[columns == 'Played'] = 'Pld'
	columns[columns == 'Points'] = 'Pts'		

	lencols = len(columns)

	# Create empty pandas dataframe
	df = pd.DataFrame(columns = columns, index = range(1, lenrows))

	# Fill the dataframe
	for i in range(1, lenrows):
		team = rows[i].find_all('td')
		df.Team.ix[i] = team[np.where(df.columns == 'Team')[0][0]].a.get_text().encode('ascii', 'ignore')
		df.Pld.ix[i] = team[np.where(df.columns == 'Pld')[0][0]].get_text().encode('ascii', 'ignore')
		df.W.ix[i] = team[np.where(df.columns == 'W')[0][0]].get_text().encode('ascii', 'ignore')
		df.D.ix[i] = team[np.where(df.columns == 'D')[0][0]].get_text().encode('ascii', 'ignore')
		df.L.ix[i] = team[np.where(df.columns == 'L')[0][0]].get_text().encode('ascii', 'ignore')
		df.GF.ix[i] = team[np.where(df.columns == 'GF')[0][0]].get_text().encode('ascii', 'ignore')
		df.GA.ix[i] = team[np.where(df.columns == 'GA')[0][0]].get_text().encode('ascii', 'ignore')
		df.GD.ix[i] = team[np.where(df.columns == 'GD')[0][0]].get_text().encode('ascii', 'ignore')

	df = df[['Team', 'Pld', 'W', 'D', 'L', 'GF', 'GA', 'GD']]

	# Add year column 
	year = wpage.split('/')[-1].split('_')[0]
	df['year'] = year
	df['league'] = league_name

	# Replace Unicode minus sign with '-'
	mask = df.GD.apply(lambda x: ('+' in x) | ('-' in x) )
	df.GD[~mask] = '-' + df.GD[~mask]
	
	# Add ladder position from the index
	df['Pos'] = df.index

	# Transform to integers
	coltmp = ['Pos', 'Pld', 'W', 'D', 'L', 'GF', 'GA','GD']
	df[coltmp] = df[coltmp].astype(float).astype(int)

	# Redefine Pts using Italian standard scoring system
	df['Pts'] = df.W * 3. + df.D

	return df

if __name__ == '__main__':

	dff = pd.DataFrame()

	for page in final_list:
		

		h = httplib2.Http()
		resp = h.request(page, 'HEAD')

		if int(resp[0]['status']) < 400:	
			print page

			df = FootB(page, league_name(page))
			dff = dff.append(df, ignore_index = True)

#ff = grouped.aggregate(np.max)['W']
#for key, grp in grouped:
#    plt.plot(grp.aggregate(np.max)['W'], label=key)
