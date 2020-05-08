from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd
import numpy as np
from zipfile import ZipFile
import io
from time import process_time as ps
import matplotlib.pyplot as plt
import datetime
from mpi4py import MPI
import math
import sys
import shutil

#replace with your own credentials. Can be found in kaggle.json downloaded from Account page of kaggle.com
username = "subbu1996"
key = "c6105db7bbad4ffb468b6d2d3a1820a2"
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
api = KaggleApi({"username":username,"key":key})
api.authenticate()
owner_slug = "borismarjanovic"
dataset_slug = "price-volume-data-for-all-us-stocks-etfs"
start = ps()

fill_nan = -999
data_path = "datasets/stocks/"

def display_files_shawn():
    data_path = './datasets/'
    file = 'symbols_valid_meta'
    suffix = '.csv'
    file_name = data_path+file+suffix

    df_symbols = pd.read_csv(file_name) # Reads a csv file into a dataframe

    df_stock_symbols = df_symbols[df_symbols.ETF == 'N']

    print( df_stock_symbols["NASDAQ Symbol"].head(3))
    return df_stock_symbols["NASDAQ Symbol"].tolist()

def display_files():

    file_ = api.datasets_download_file('jacksoncrow','stock-market-dataset','symbols_valid_meta.csv')
    df=pd.read_csv(io.StringIO(file_.decode('utf-8')))
    files = df['Symbol'].tolist()
    return files

def read_file(f):
    ret_val = None
    try:
      #Focus on Date, Close Adj. Close from file
      c=pd.read_csv(io.StringIO(f))
      ret_val = c[['Date','Close','Adj Close']]

    except:
        print(sys.exc_info()[0])
        ret_val = None

    return ret_val

def create_labels(cur_rate):
    '''This function returns a label based on the change criteria. If the
    current value is Not a Number, then NoData is returned. If the difference
    is positive, then Up is returned. If the difference is negative, then
    Down is returned. The default returns None, since the two values are
    assumed to be equal.'''
    if cur_rate == fill_nan or cur_rate == np.nan:
        return 'NoData'
    elif cur_rate > 0:
        return 'Up' # rate goes up
    elif cur_rate < 0:
        return 'Down' # rate goes down
    else:
        return 'None' # rate has not changed

def download_files_alex(d_files, rk, limit = 0):
    i = 0
    for d in d_files:
        if (  limit > 0 and i == limit ):
          break

        i += 1
        file = api.datasets_download_file('jacksoncrow','stock-market-dataset',d)
        nf = read_file(file)

        if ( not nf.empty ):
            print(nf)
            #TODO: Filter

def load_files_shawn(symbols, rank_node):
    data_path = "datasets/"
    file = 'symbols_valid_meta'
    suffix = '.csv'
    count = 0
    hold_df = pd.DataFrame()
    for symbol in symbols:

        count += 1
        file_name = symbol+suffix
        work_df = pd.read_csv(file_name, index_col=0)
        work_df.drop(columns = ['Open','High','Low','Close','Volume'], inplace=True)
        work_df.rename(columns={'Adj Close':symbol}, inplace=True)
        if hold_df.empty:
            hold_df = pd.DataFrame().reindex_like(work_df)
            hold_df[symbol] = work_df[symbol].pct_change()

        else:
            hold_df[symbol] = work_df[symbol].pct_change()
    return hold_df

def download_to_local(r):
    print('Downloading Files')
    #file_ = api.dataset_download_files('jacksoncrow/stock-market-dataset',unzip = True,path = './datasets')
    print('Download_complete')
def download_files(d_files,r):
    start_date = '01-01-2009'
    end_date = '08-01-2010'
    final = pd.DataFrame()
    for d in d_files:
        d1 = 'datasets/stocks/'+d+'.csv'

        try:
                df = pd.read_csv(d1)
                df.drop(columns = ['Open','High','Low','Close','Volume'],inplace = True)
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.loc[start_date : ]
                df.rename(columns={"Adj Close":d},inplace = True)
                df.set_index('Date', inplace=True)
                final = pd.concat([final,df],axis = 1)
        except Exception as e:
                print('Rank: ',r,' - exception: ',e)
                #print('Error in file',d)
                pass
    final = final.pct_change()
    #final.fillna(fill_nan, inplace = True)
    comm.send(final,dest = 0)

def plt_df_chg( df, title_df, graph_df, tail = 120):

    graph_title = title_df + '\nFull' + str(tail)+ ' Days'
    graph_file = graph_df + str(tail) + '.png'
    df[[ 'None', 'Down', 'Up']].tail(tail).plot(kind='bar',\
                         stacked=True, \
                         title=graph_title)
    plt.xticks([])
    plt.show()
    #plt.savefig( graph_file, bbox_inches='tight')

if rank == 0:
	start_1 = '08-01-2009'
	end_1 = '08-01-2010'
	start_2 = '04-01-2019'
	end_2 = '04-01-2020'

	download_to_local(rank)
	files = display_files_shawn()
	files_num = 1000


	opti_num = math.floor(files_num/(size-1))
	reminder = files_num%(size-1)
	count = 0
	final_df = pd.DataFrame()
	print("Rank ",rank,"length ",files_num)
	data = {'key1':[opti_num,reminder], 'key2':files}
	'''for i in range(1, size):
            if reminder - count == 0:
                comm.send(files[opti_num*(i-1):opti_num*i],dest = i)
                print("rank: ", i, opti_num*(i-1), opti_num*i)
            else:
                comm.send(files[opti_num*(i-1) + count:opti_num*i + count],dest = i)
                print("rank: ", i, opti_num*(i-1) + count, opti_num*i + count)
                reminder -= 1
                count += 1
            print("Source: ",i)    
            df = comm.recv(source = i)
            final_df = pd.concat([final_df,df],axis = 1)
	#final_df = pd.concat([final_df,df],axis = 1)
	hold_mean_df = final_df.sum(axis=1)
	length = len(final_df)

	final_df.fillna(fill_nan, inplace= True)
	hold_change_df = pd.DataFrame().reindex_like(final_df)

	# Create labels for positive, negative or zero change
	for symbol in final_df:
		hold_change_df[symbol]= list(map(create_labels,final_df[symbol]))

	final_changed_df = hold_change_df.apply(pd.Series.value_counts, axis=1)
	final_pct_changed_df = final_changed_df.loc[:, ('None', 'Down', 'Up')]
	final_pct_changed_df["Up"] = final_changed_df.loc[:, ("Up")]/(length - final_changed_df.loc[:, ('NoData')])
	final_pct_changed_df["Down"] = final_changed_df.loc[:, ("Down")]/(length - final_changed_df.loc[:, ('NoData')])
	final_pct_changed_df["None"] = final_changed_df.loc[:, ("None")]/(length - final_changed_df.loc[:, ('NoData')])

	mean_df = hold_mean_df/(length - final_changed_df.loc[:, ('NoData')]) # Use only number of stocks that are being listed; No Data likely means stock has no IPO yet
	pandemic1_pct_chg = final_pct_changed_df[ start_1 : end_1 ]
	pandemic2_pct_chg = final_pct_changed_df[ start_2 : end_2 ]

	plt_df_chg( final_pct_changed_df[start_1 : end_1], \
	"Percent of Stocks as Change\n Stocks - H1N1", \
	"pct_stock_chg1_full", tail = 180 )
	plt_df_chg( final_pct_changed_df[start_2 : end_2], \
	"Percent of Stocks as Change\n Stocks - COVID-19", \
	"pct_stock_chg2_full", tail = 180 )
	plt_df_chg( pandemic1_pct_chg[[ 'None', 'Down', 'Up']], \
	"Percent of Stocks as Change\nH1N1", \
	"pct_pandemic1_chg_full", tail = 120)
	plt_df_chg( pandemic2_pct_chg[[ 'None', 'Down', 'Up']], \
	"Percent of Stocks as Change\COVID-19", \
	"pct_pandemic2_chg_full", tail = 120)
	hold_mean_df[hold_mean_df < 40000].tail(120).plot.line(\
	title="Mean Percent Change\n RE: COVID-19")
	#plt.xticks([])
	plt.show()
	#plt.savefig("mn_pct_chg-COVID-19.png", bbox_inches='tight')
	print(final_df.info)
	#shutil.rmtree('datasets')'''
else:
	'''hold_work = pd.DataFrame()
	hold_final = pd.DataFrame()
	changed_df = pd.DataFrame()

	print('Process at Rank: ',rank,    hold_work = pd.DataFrame()
    hold_final = pd.DataFrame()
    changed_df = pd.DataFrame()

    print('Process at Rank: ',rank,'started')
    v = data["key1"]
    files = data["key2"]


    print("Rank: ",rank, "Files: ", files[v[0]*(rank-1):v[0]*rank])


    hold_work_df = download_files(files[v[0]*(rank-1):v[0]*rank],rank)
    hold_work = download_files(files[v[0]*(rank-1):v[0]*rank],rank)
    hold_work.fillna(fill_nan, inplace = True)
    changed_df = labels(files[v[0]*(rank-1):v[0]*rank], hold_work)

    final = hold_work.pct.change()

    comm.send(final,dest = 0, tag = 0)
    comm.send(changed_df, dest = 0, tag = 1)'started')
	data = comm.recv(source = 0)
	print("")


	#hold_work_df = download_files(data,rank)
	download_files(data,rank)
	#hold_work.fillna(fill_nan, inplace = True)
	#changed_df = labels(data, hold_work)

	#final = hold_work.pct.change()

	#comm.send(final,dest = 0)
	#comm.send(changed_df, dest = 0)'''
	data = None
data = comm.bcast(data, root=0)
	

if rank > 0:
    hold_work = pd.DataFrame()
    hold_final = pd.DataFrame()
    changed_df = pd.DataFrame()

    print('Process at Rank: ',rank,'started')
    v = data["key1"]
    files = data["key2"]


    print("Rank: ",rank, "Files: ", files[v[0]*(rank-1):v[0]*rank])


    #hold_work_df = download_files(files[v[0]*(rank-1):v[0]*rank],rank)
    download_files(files[v[0]*(rank-1):v[0]*rank],rank)
    #hold_work.fillna(fill_nan, inplace = True)
    #changed_df = labels(files[v[0]*(rank-1):v[0]*rank], hold_work)

    #final = hold_work.pct.change()

    #comm.send(final,dest = 0, tag = 0)
    #comm.send(changed_df, dest = 0, tag = 1)
if rank == 0:
    for i in range(1, size):
        df = comm.recv(source = i)
        final_df = pd.concat([final_df,df],axis = 1)
    hold_mean_df = final_df.sum(axis=1)
    length = len(final_df)

    final_df.fillna(fill_nan, inplace= True)
    hold_change_df = pd.DataFrame().reindex_like(final_df)
    
    # Create labels for positive, negative or zero change
    for symbol in final_df:
        hold_change_df[symbol]= list(map(create_labels,final_df[symbol]))
        
    final_changed_df = hold_change_df.apply(pd.Series.value_counts, axis=1)
    final_pct_changed_df = final_changed_df.loc[:, ('None', 'Down', 'Up')]
    final_pct_changed_df["Up"] = final_changed_df.loc[:, ("Up")]/(length - final_changed_df.loc[:, ('NoData')])
    final_pct_changed_df["Down"] = final_changed_df.loc[:, ("Down")]/(length - final_changed_df.loc[:, ('NoData')])
    final_pct_changed_df["None"] = final_changed_df.loc[:, ("None")]/(length - final_changed_df.loc[:, ('NoData')])

    mean_df = hold_mean_df/(length - final_changed_df.loc[:, ('NoData')]) # Use only number of stocks that are being listed; No Data likely means stock has no IPO yet
    pandemic1_pct_chg = final_pct_changed_df[ start_1 : end_1 ]
    pandemic2_pct_chg = final_pct_changed_df[ start_2 : end_2 ]

    plt_df_chg( final_pct_changed_df[start_1 : end_1], \
    "Percent of Stocks as Change\n Stocks - H1N1", \
    "pct_stock_chg1_full", tail = 180 )
    plt_df_chg( final_pct_changed_df[start_2 : end_2], \
    "Percent of Stocks as Change\n Stocks - COVID-19", \
    "pct_stock_chg2_full", tail = 180 )
    plt_df_chg( pandemic1_pct_chg[[ 'None', 'Down', 'Up']], \
    "Percent of Stocks as Change\nH1N1", \
    "pct_pandemic1_chg_full", tail = 120)
    plt_df_chg( pandemic2_pct_chg[[ 'None', 'Down', 'Up']], \
    "Percent of Stocks as Change\COVID-19", \
    "pct_pandemic2_chg_full", tail = 120)
    hold_mean_df[hold_mean_df < 40000].tail(120).plot.line(\
    title="Mean Percent Change\n RE: COVID-19")
    plt.show()
    #plt.savefig("mn_pct_chg-COVID-19.png", bbox_inches='tight')
    print(final_df.info)
    #shutil.rmtree('datasets')

print(ps()-start, rank)
