import cbpro, time
import websocket, json, pprint, talib, numpy
import config
import itertools
from cbpro.authenticated_client import AuthenticatedClient
from cbpro.cbpro_auth import get_auth_headers


#RSI stuff

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'BTCUSD'
TRADE_QUANTITY = 0.00

closes = []
in_position = False

client = cbpro.PublicClient()

SOCKET = "wss://ws-feed.pro.coinbase.com/"


# get live price via coinbase pro realtime data

ticker = client.get_product_ticker('BTC-USD')
print(ticker['price'])
print(ticker['time'])
print(ticker['bid'])
print(ticker['ask'])

# mathematical testing bullshit

bid = int(float(ticker['bid']))
ask = int(float(ticker['ask']))

sum = bid+ask

average = (sum)/2
print('the average of the bid/ask spread is: ', average)

auth_client = cbpro.AuthenticatedClient(config.api_key, config.api_secret, config.passphrase)
# sandbox API (test stuff, ignore vvvvv)
# auth_client = cbpro.AuthenticatedClient(key, b64secret, passphrase,
#                                   api_url="https://api-public.sandbox.pro.coinbase.com")

# order definition

def order(side, price, size, product_id, order_type):
    try:
        print("sending order")
        order = auth_client.place_market_order(side=side, price=price,size=size,product_id=product_id,order_type=order_type)
        print(order)
    except Exception as e:
        print("An exception occurred - {}".format(e))
        return False

    return True

# connection

class myWebsocketClient(cbpro.WebsocketClient):

    def on_open(ws):
        ws.url = "wss://ws-feed.pro.coinbase.com/"
        ws.products = ["BTC-USD"]
        ws.message_count = 0
        print("Lets count the messages!")

    def on_close(ws):
        print("closed connection")

    def on_message(ws, msg):
        global closes, in_position
        print('received message')
        print(msg)
        json_message = json.loads(msg)
        pprint.pprint(json_message)

        candle = json_message['k']

        is_candle_closed = candle['x']
        close = candle['c']

        if is_candle_closed:
            print("candle closed at {}".format(close))
            closes.append(float(close))
            print("closes")
            print(closes)

            if len(closes) > RSI_PERIOD:
                np_closes = numpy.array(closes)
                rsi = talib.RSI(np_closes,RSI_PERIOD)
                print("All RSIs calculated so far")
                print(rsi)
                last_rsi = rsi[-1]
                print("The current RSI is {}".format(last_rsi))

                if last_rsi > RSI_OVERBOUGHT:
                    if in_position:
                        print("Overbought - sell now")
                        # put cb sell logic here
                        order_succeeded = order(side='sell',size='0.00',product_id='BTC')
                        if order_succeeded:
                            in_position = False

                    else:
                        print("It is overbought, but we do not own any {}".format(ticker))

                if last_rsi > RSI_OVERSOLD:
                    if in_position:
                        print("{} is oversold, but you already own it, nothing to do".format(ticker))
                    else:
                        print("Oversold - buy now")
                        #put cb buy logic here
                        order_succeeded = order(side='buy',size='0.00',product_id='BTC')
                        if order_succeeded:
                            in_position = True

    ws = websocket.WebSocketApp(SOCKET, on_open=on_open,on_close=on_close,on_message=on_message)
    ws.run_forever()





# wsClient = myWebsocketClient()
# wsClient.start()
# print(wsClient.url, wsClient.products)
# while (wsClient.message_count < 500):
#     print ("\nmessage count =", "{} \n".format(wsClient.message_count))
#     time.sleep(1)
# wsClient.close()



# d = {0:2}
# print(d[0])