# coding: utf -8
import PySimpleGUI as sg # ライブラリの読み込み
import threading
import sys
import socket
from socket import socket, AF_INET, SOCK_DGRAM ,SOCK_STREAM
import time

# バッファサイズ指定
BUFSIZE = 14600
# テーマの設定
sg.theme("SystemDefault ")

# 事前設定
L1 = [[sg.Text("・IP address "            ,size=(20,1)),
    sg.InputText(default_text="127.0.0.2" ,     text_color = "#000000",background_color ="#ffffff" ,    size=(40,1),    key="-IP_GW" )],
    [sg.Text("・port num "            ,size=(20,1)),
    sg.InputText(default_text="30490" ,            text_color = "#000000",background_color ="#ffffff" ,    size=(40,1),    key="-PORT_GW-" )]
]
# UDP
L2 = [[sg.Button("OPEN", border_width=4 ,    size =(25,1),    key="-BTN_UDP_OPEN-")]]

# TCP
L3 = [[sg.Button("OPEN", border_width=4 ,     size =(25,1),    key="-BTN_TCP_OPEN-")]]

# 通信ステータス
L4 = [[sg.Multiline(default_text="", border_width=1,    size=(62,10),    key="-COM_ST-")]]

L = [[sg.Frame("Socket config",L1)],
    [sg.Frame("UDP",L2),sg.Frame("TCP",L3)],
    [sg.Frame("Connection status",L4)]]

# ウィンドウ作成
window = sg.Window ("SOME/IP sever tool", L)
values = ""

def main():
    global values
    threads = []
    # イベントループ
    while True:
        # イベントの読み取り（イベント待ち）
        event , values = window.read()
        # 確認表示
        # print(" イベント:",event ,", 値:",values)
        # 終了条件（ None: クローズボタン）
        if event == "-BTN_UDP_OPEN-":
            t1 = threading.Thread(target=udp_recv, args=(values['-IP_GW'] , int(values['-PORT_GW-']),))
            threads.append(t1)
            t1.setDaemon(True)
            t1.start()
            window["-COM_ST-"].Update("----------UDP open----------")

        # TCP接続
        elif event == "-BTN_TCP_OPEN-":
            t2 = threading.Thread(target=tcp_recv, args=(values['-IP_GW'] , int(values['-PORT_GW-']),))
            threads.append(t2)
            t2.setDaemon(True)
            t2.start()
            window["-COM_ST-"].Update("----------TCP open----------")
        elif event == None:
            sys.exit()


def main_window_update_open():
    global values
    window_txt = "----------TCP connect----------\n"
    window["-COM_ST-"].Update(window_txt)
    print(window_txt)
    return


def main_window_update(protocol,recv_msg,data,send_msg,send_data):
    global values
    window_txt = ""
    window_txt += "----------{} request recieve----------\n".format(protocol) \
                + "Message Type:" + recv_msg + "\n" \
                + "Request data:" + data + "\n"
    if "" != send_msg:
        window_txt += "\n----------{} responce send----------\n".format(protocol) \
                + "Return Code:" + send_msg + "\n" \
                + "Responce data:" + send_data + "\n"
    window["-COM_ST-"].Update(window_txt)
    print(window_txt)
    return


def main_window_update_close():
    global values
    window_txt = "----------TCP disconnect----------\n"
    window["-COM_ST-"].Update(window_txt)
    print(window_txt)
    return


def udp_recv( ip_addr , port ):
    protocol = "UDP"
    # 受信側アドレスをtupleに格納
    SrcAddr = ( ip_addr , port)
    # ソケット作成
    udpServSock = socket(AF_INET, SOCK_DGRAM)
    # 受信側アドレスでソケットを設定
    udpServSock.bind(SrcAddr)
    time.sleep(1)
    # While文を使用して常に受信待ちのループを実行
    while True:
        time.sleep(1)
        # ソケットにデータを受信した場合の処理
        # 受信データを変数に設定
        data, addr = udpServSock.recvfrom(BUFSIZE)
        # 受信データを確認
        recv_msg,data,send_msg,send_data = someip_recv_msg(data.hex(),protocol)
        main_window_update(protocol,recv_msg,data,send_msg,send_data)
        if None != send_data:
            send_data = bytes.fromhex(send_data)
            udpServSock.sendto(send_data,addr)


def recv_client(connection, client):
    protocol = "TCP"
    while True:
        try:
            data = connection.recv(BUFSIZE)
            if 0 != len(data):
                recv_msg,data,send_msg,send_data = someip_recv_msg(data.hex(),protocol)
                main_window_update(protocol,recv_msg,data,send_msg,send_data)
                if None != send_data:
                    connection.send(bytes.fromhex(send_data))
            else:
                break
        except ConnectionResetError:
            break
    connection.close()
    main_window_update_close()


def tcp_recv( ip_addr , port ):
    tcp_server = socket(AF_INET, SOCK_STREAM)
    tcp_server.bind(( ip_addr , port))
    tcp_server.listen()
    time.sleep(1)
    while True:
        (connection, client) = tcp_server.accept()
        main_window_update_open()
        thread = threading.Thread(target=recv_client, args=(connection, client))
        # スレッド処理開始
        thread.start()


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


# 受信データ判定関数
def someip_recv_msg(data,protocol):
    recv_msg = ""
    msg_type = data[28:30]
    for key,value in someip_msg_type.items():
        if value==msg_type.lower():
            recv_msg = key
    rtn_code = "E_OK"
    send_data = list(data)
    send_data[30] = someip_rtn_code["E_OK"][0]
    send_data[31] = someip_rtn_code["E_OK"][1]
    return recv_msg,data,rtn_code,data


if __name__ == '__main__':
    main()

