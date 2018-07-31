from shutil import copyfile
import datetime
import json
import time
import urllib.parse
import urllib.request
import smtplib

DEBUG = False

def send_email(msg):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    #email and password redacted
    server.login("redacted_email", "redacted_password")
    #email redacted
    server.sendmail("email_redacted", "email_redacted", msg)
    server.quit()

def copy_file(file1: str, file2: str) -> None:
    '''copies old file to new file'''
    try:
        now = datetime.datetime.now()
        name = file2.split('.')
        filename = name[0]+str(now.hour)+'-'+str(now.minute)+'-'+str(now.second)+'.'+name[1]
        if DEBUG:
            print('Copying File...')
        copyfile(file1, filename)
        if DEBUG:
            print('Copying Completed')
    except:
        if DEBUG:
            print ('File Not Found')

def get_result(url: str) -> dict:
    '''
    This function takes a URL and returns a Python dictionary representing the
    parsed JSON response.
    '''
    response = None
    
    try:
        # Here, we open the URL, which gives us back a response.
        if DEBUG:
            print ('requesting server for data')
        while True:
            try:
                response = urllib.request.urlopen(url, timeout = 5)
                break
            except:
                print (get_current_time(),'Server Timed Out, Trying Again in 30s')
                time.sleep(30)

        # Next, we pass that response object to the json.load()
        # function, which will read its bytes and convert them
        # to the analogous Python object instead.
        if DEBUG:
            print ('returning server reponse')
        return json.load(response)

    finally:
        # We'd better not forget to close the response when we're done,
        # assuming that we successfully opened it.
        if response != None:
            response.close()

def get_coinmarketcap_prices() -> dict:
    queries = get_query([('limit', 0)])
    data =(get_result("https://api.coinmarketcap.com/v1/ticker/?" + queries))
    prices = dict()
    for record in data:
        prices[record['symbol']] = record['price_usd']
    return prices

def get_gdax_prices() -> dict:
    products = ['BTC', 'BCH', 'ETH', 'LTC']
    prices = dict()
    for currency in products:
        book = get_result('https://api.gdax.com/products/' + str(currency) + '-USD/book?level=1')
        prices[currency] = float(book['asks'][0][0])
    return prices

def get_gdax_historic_prices() -> []:
    params = urllib.parse.urlencode([('granularity', 60)])
    #book = get_result('https://api.gdax.com/products/BTC-USD/book?level=2')
    book = get_result('https://api.gdax.com/products/BTC-USD/candles?' + params)
    structured_list = []
    for each in book:
        date = datetime.datetime.fromtimestamp(each[0]).strftime('%Y-%m-%d %H:%M:%S')
        temp_dict= dict()
        temp_dict['time'] = date
        temp_dict['low'] = each[1]
        temp_dict['high'] = each[2]
        temp_dict['open'] = each[3]
        temp_dict['close'] = each[4]
        temp_dict['vol'] = each[5]
        structured_list.append(temp_dict)
    for record in structured_list:
        print(record)
    #print (type(book))

class Log:
    def __init__(self) -> None:
        now = datetime.datetime.now()
        self.filename = 'log '+str(now.year-2000)+'-'+str(now.month)+'-'+str(now.day)+' '+str(now.hour)+'-'+str(now.minute)+'-'+str(now.second)+'.txt'

    def set_name_to(self, name: str) -> None:
        self.filename = name

    def append_to_file(self, *args, sep = ' ') -> None:
        str_to_write = ''
        for each in args:
            str_to_write += str(each) + sep
        file = open(self.filename,"a+")
        file.write(get_current_time() + '- ' + str(str_to_write[:-1]) + '\n')
        file.close()

    def write_to_file(self, *args, sep = ' ') -> None:
        str_to_write = ''
        for each in args:
            str_to_write += str(each) + sep
        file = open(self.filename,"w+")
        file.write(get_current_time() + '- ' + str(str_to_write[:-1]) + '\n')
        file.close()
        
    def get_filename(self) -> str:
        return self.filename


def get_query(queries: [tuple]) -> str:
    return urllib.parse.urlencode(queries)

def get_current_time() -> str:
    now = datetime.datetime.now()
    #return now.isoformat()
    #print(time.time()) #ISO Format
    return (str(now.month)+ '/' + str(now.day) + '/' + str(now.year-2000) + ' ' + str(now.hour) + ':' + str(now.minute) + ':' + str(now.second))

def run() -> None:
    
    purchase_price = 0
    funds = 100
    track = dict()
    #track['BTC'] = (4000,5000)
    track['ETH'] = (400, 500)
    print ('Running Price Tracker')
    for each in track:
        print (each, '-> Lower:', track[each][0], 'Upper:', track[each][1])
    min_price = 400
    max_price = 500
    log = Log()
    
    while True:
        prices = get_gdax_prices()
        #prices = get_coinmarketcap_prices()
        for coin, price in prices.items():
            if coin in track:
                lower, upper = track[coin]
                print('Analyzing Prices for', coin)
                if lower < price < upper:
                    pass
                    print (get_current_time(), '=>', coin,': ', lower,' <', price, '> ', upper, sep = '')
                if price <= lower:
                    if purchase_price == 0:
                        possible_min_price = 1.01 * price
                        if possible_min_price < min_price:
                            print("Changing Min Price from", min_price, "to", possible_min_price)
                            min_price = possible_min_price
                            log.append_to_file('New Min Price:',min_price)
                        if price > min_price:
                            purchase_price  = price
                            print (get_current_time(), ' Purchased', coin, price, format(funds, '0.2f'))
                            log.append_to_file('Purchased', coin, price, format(funds, '0.2f'))
                            #send_email('Purchased @'+ str(price))
                if price >= upper:
                    if purchase_price != 0:
                        possible_max_price = 0.99 * price
                        if possible_max_price > max_price:
                            print("Changing Max Price from", max_price, "to", possible_max_price)
                            max_price = possible_max_price
                            log.append_to_file('New Max Price:',max_price)
                        if price < max_price:                            
                            funds = funds * (price/purchase_price)
                            print (get_current_time(), ' Sold', coin, price, format(funds, '0.2f'))
                            log.append_to_file('Sold', coin, price, format(funds, '0.2f'))
                            purchase_price = 0
                            #send_email('Sold @'+ str(price) + ' Funds:' + str(funds))
                
        print('Waiting 30 seconds...')        
        for i in range(10):
            time.sleep(0.5)

if __name__ == '__main__':
    run()
    
        


