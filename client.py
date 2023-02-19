# coding: utf -8
import PySimpleGUI as sg # ライブラリの読み込み
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
# バッファサイズ指定
BUFSIZE = 14600
# テーマの設定
sg.theme("SystemDefault ")

# 事前設定
L1 = [
    # 診断機設定
    [sg.Text("・src IP address ",size=(15,1)),
    sg.InputText(default_text="127.0.0.1" , text_color = "#000000",background_color ="#ffffff",        size=(15,1),    key="-SRC_IP_ADDR-" ),
    sg.Text("     ")],
    [sg.Text("・src port num  ",size=(15,1)),
    sg.InputText(default_text="30490" ,    text_color = "#000000",background_color ="#ffffff" ,        size=(8,1),        key="-SRC_PORT_NUM-" )],
    [sg.Text("・dest IP address ",size=(15,1)),
    sg.InputText(default_text="127.0.0.2" , text_color = "#000000",background_color ="#ffffff" ,    size=(15,1),    key="-DEST_IP_ADDR-" ),
    sg.Text("     ")],
    [sg.Text("・dest port num  ",size=(15,1)),
    sg.InputText(default_text="30490" ,    text_color = "#000000",background_color ="#ffffff" ,        size=(8,1),        key="-DEST_PORT_NUM-" )],
 ]

# UDP
L2 = [[sg.Button("send", border_width=4 ,    size =(10,1),    key="-BTN_SEND_UDP-")]
]

# TCP
L3 = [[sg.Button("connect", border_width=4 , size =(10,1),    key="-BTN_CONECT_TCP-"),
    sg.Button("send", border_width=4 ,         size =(10,1),    key="-BTN_SEND_TCP-"),
    sg.Button("disconnect", border_width=4 , size =(10,1),    key="-BTN_DISSCONECT_TCP-")]
]

# SOME/IP Parameter
L4 = [
    [sg.Text("・Message ID ", size=(17,1)) , sg.InputText(default_text="00000001" ,    size=(12,1) ,    key="-MESSAGE_ID-")],
    [sg.Text("・Length ",size=(17,1)),    sg.InputText(default_text="00000008" ,    size=(12,1) ,        key="-LENGTH-" ),
    sg.Button("Auto set", border_width=4 ,    size =(10,1),    key="-BTN_LENGTH_SET-")],
    [sg.Text("・Request ID ", size=(17,1)) , sg.InputText(default_text="00000001" ,    size=(12,1) ,    key="-REQUEST_ID-")],
    [sg.Text("・Protcol Version ", size=(17,1)) , sg.InputText(default_text="01" ,    size=(4,1) ,    key="-PROT_VER-")],
    [sg.Text("・Interface Version ", size=(17,1)) , sg.InputText(default_text="01" ,    size=(4,1) ,key="-IF_VER-")],
    [sg.Text("・Message Type ", size=(17,1)) , sg.InputText(default_text="00" ,    size=(4,1) ,        key="-MESSAGE_TYPE-")],
    [sg.Text("・Return Code ", size=(17,1)) , sg.InputText(default_text="00" ,    size=(4,1) ,        key="-RTN_CODE-")],
    [sg.Text("・Payload ", size=(17,1))],
    [sg.Multiline(default_text="" , border_width=2,        size=(55,8),    key="-PAYLOAD-")]
]

L5 = [
    [sg.Multiline(default_text="", border_width=1,    size=(58,26),autoscroll=True,    key="-COM_ST-")]]

L =[
    [
    sg.Frame("Settings",
        [
            [sg.Frame("Socket config ",L1,size=(420,130))],
            [sg.Frame("SOME/IP Parameter",L4)]
        ]
    ),
    sg.Frame("SOME/IP communication",
        [
            [sg.Frame("UDP",L2),sg.Frame("TCP",L3)],
            [sg.Frame("Connection status",L5)]
        ]
    ),
    ]
]

L_NEW = []

# ウィンドウ作成
window = sg.Window ("SOME/IP cliant tool", L)
values = ""

def main():
    global values
    # イベントループ
    while True:
        # イベントの読み取り（イベント待ち）
        event , values = window.read()
        window_txt = ""
        # 確認表示
        # print(" イベント:",event ,", 値:",values)
        # 終了条件（ None: クローズボタン）
        if event == "-BTN_SEND_UDP-":
            window_txt += "----------UDP request send----------"
            window_txt += main_udp_send_cmd(values)
        elif event == "-BTN_CONECT_TCP-":
            tcp_connect( values['-SRC_IP_ADDR-'] , values['-DEST_IP_ADDR-'] , int(values['-SRC_PORT_NUM-']) , int(values['-DEST_PORT_NUM-']) )
            window_txt +=  "----------TCP connect----------\n"
        elif event == "-BTN_SEND_TCP-":
            window_txt += "----------TCP request send----------\n"
            window_txt += main_tcp_send_cmd(values)
        elif event == "-BTN_DISSCONECT_TCP-":
            tcp_close()
            window_txt +=  "----------TCP disconnect----------\n"
            window["-SRC_PORT_NUM-"].Update( int(values["-SRC_PORT_NUM-"]) + 1)
        elif event == "-BTN_LENGTH_SET-":
            window_txt +=  "----------Length update----------\n"
            length = "{:08X}".format(8 + int(len(values["-PAYLOAD-"].replace("\n",""))/2) )
            window["-LENGTH-"].Update(length)
        elif event == None:
            print(" 終了します． ")
            break
        print(window_txt.replace("\n\n\n","\n\n"))
        window["-COM_ST-"].Update(values['-COM_ST-']+ "\n\n" + window_txt.replace("\n\n\n","\n\n"))
    # 終了処理
    window.close()


def main_udp_send_cmd(values):
    rtn = ""
    send_msg , send_data = someip_make_msg(values,"UDP")
    if None != send_msg:
        rtn =  "\nMessage Type:" + send_msg + "\n" \
            + "Request data:" + send_data.upper()+ "\n\n"
        rtn += udp_send( values['-SRC_IP_ADDR-'] , values['-DEST_IP_ADDR-'] , int(values['-SRC_PORT_NUM-']) , int(values['-DEST_PORT_NUM-']) , bytes.fromhex(send_data) )
    return rtn


def udp_send( src_ip , dst_ip , src_port , dst_port , data ):
    rtn = ""
    # 送信側アドレスをtupleに格納
    SrcAddr = ( src_ip , src_port )
    # 受信側アドレスをtupleに格納
    DstAddr = ( dst_ip , dst_port )
    # ソケット作成
    udpClntSock = socket(AF_INET, SOCK_DGRAM)
    # 送信側アドレスでソケットを設定
    udpClntSock.bind(SrcAddr)
    # 受信側アドレスに送信
    udpClntSock.sendto(data,DstAddr)

    # While文を使用して常に受信待ちのループを実行
    while True:
        # ソケットにデータを受信した場合の処理
        # 受信データを変数に設定
        data, addr = udpClntSock.recvfrom(BUFSIZE)
        rtn = main_recv_cmd(data.hex(),"UDP")
        break
    return rtn


def tcp_connect( src_ip , dst_ip , src_port , dst_port ):
    global tcpClntSock
    # ソケット作成
    tcpClntSock = socket(AF_INET, SOCK_STREAM)
    tcpClntSock.settimeout(0.5)
    # 送信側アドレスをtupleに格納
    SrcAddr = ( src_ip , src_port )
    # 送信側アドレスでソケットを設定
    tcpClntSock.bind(SrcAddr)
    # サーバーに接続
    tcpClntSock.connect((dst_ip, dst_port))


def tcp_close():
    global tcpClntSock
    # ソケットクローズ
    tcpClntSock.close()


def main_tcp_send_cmd(values):
    rtn = ""
    send_msg , send_data = someip_make_msg(values,"TCP")
    if None != send_msg:
        rtn =  "Message Type:" + send_msg + "\n" \
            + "Request data:" + send_data.upper()+ "\n\n"
        rtn += tcp_send( bytes.fromhex(send_data) )
    return rtn


def tcp_send( data ):
    global tcpClntSock
    rtn = ""
    try:
        tcpClntSock.send(data)
        response = tcpClntSock.recv(4096)
        rtn = main_recv_cmd(response.hex(),"TCP")
    except ConnectionResetError:
        # ソケットクローズ
        tcpClntSock.close()
    return rtn


def main_recv_cmd(data,protcol):
    global values
    global window
    window_txt = ""
    recv_msg = someip_recv_msg(data,protcol)
    if None != recv_msg:
        window_txt = "----------{} responce recieve----------\n".format(protcol) \
                      + "Return Code:" + recv_msg + "\n" \
                      + "Responce data:" + data.upper() + "\n"
    return window_txt


# Message Type
someip_msg_type = \
{
    "REQUEST"                :"00" ,
    "REQUEST_NO_RETURN"      :"01" ,
    "NOTIFICATION"           :"02" ,
    "RESPONSE"               :"80" ,
    "ERROR"                  :"81" ,
    "TP_REQUEST"             :"20" ,
    "TP_REQUEST_NO_RETURN"   :"21" ,
    "TP_NOTIFICATION"        :"22" ,
    "TP_RESPONSE"            :"a0" ,
    "TP_ERROR"               :"a1"
}

# Return Code
someip_rtn_code = \
{
    "E_OK"                       :"00",
    "E_NOT_OK"                   :"01",
    "E_UNKNOWN_SERVICE"          :"02",
    "E_UNKNOWN_METHOD"           :"03",
    "E_NOT_READY"                :"04",
    "E_NOT_REACHABLE"            :"05",
    "E_TIMEOUT"                  :"06",
    "E_WRONG_PROTOCOL_VERSION"   :"07",
    "E_WRONG_INTERFACE_VERSION"  :"08",
    "E_MALFORMED_MESSAGE"        :"09",
    "E_WRONG_MESSAGE_TYPE"       :"0a",
    "E_E2E_REPEATED"             :"0b",
    "E_E2E_WRONG_SEQUENCE"       :"0c",
    "E_E2E"                      :"0d",
    "E_E2E_NOT_AVAILABLE"        :"0e",
    "E_E2E_NO_NEW_DATA"          :"0f"
}


# 送信データ作成関数
def someip_make_msg(values,protocol):
    send_msg = ""
    for key,value in someip_msg_type.items():
        if value==values["-MESSAGE_TYPE-"].lower():
            send_msg = key
    send_data = values["-MESSAGE_ID-"]  \
                + values["-LENGTH-"] \
                + values["-REQUEST_ID-"] \
                + values["-PROT_VER-"] \
                + values["-IF_VER-"] \
                + values["-MESSAGE_TYPE-"] \
                + values["-RTN_CODE-"] \
                + values["-PAYLOAD-"]
    return send_msg ,send_data


# 受信データ判定関数
def someip_recv_msg(data,protocol):
    rtn =""
    rtn_code = data[30:32]
    for key,value in someip_rtn_code.items():
        if value==rtn_code.lower():
            rtn = key
    return rtn


if __name__ == '__main__':
    main()