"""
This file is part of Ari_Shogi-Server-Client

Copyright (c) 2023 YuaHyodo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from threading import Thread
from datetime import datetime
import codecs
import socket
import time

class Client:
    def __init__(self, host, port=4081, log_file=None):
        self.host = host
        self.port = port
        self.buf_size = 1024
        self.keep_connect = [False, False]
        self.log_file = log_file

        self.d1 = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e', '6': 'f', '7': 'g', '8': 'h', '9': 'i'}
        self.d2 = {v: k for k, v in self.d1.items()}
        self.d3 = {'P': 'FU', 'p': 'FU', 'L': 'KY', 'l': 'KY', 'N': 'KE', 'n': 'KE', 'S': 'GI', 's': 'GI',
                   'G': 'KI', 'g': 'KI', 'B': 'KA', 'b': 'KA', 'R': 'HI', 'r': 'HI', 'K': 'OU', 'k': 'OU',
                   '+P': 'TO', '+p': 'TO', '+L': 'NY', '+l': 'NY', '+N': 'NK', '+n': 'NK', '+S': 'NG', '+s': 'NG',
                   '+B': 'UM', '+b': 'UM', '+R': 'RY', '+r': 'RY'}
        self.d4 = {'+P': 'TO', '+p': 'TO', '+L': 'NY', '+l': 'NY', '+N': 'NK', '+n': 'NK', '+S': 'NG', '+s': 'NG',
                   '+B': 'UM', '+b': 'UM', '+R': 'RY', '+r': 'RY'}
        self.d5 = {'P': 'FU', 'L': 'KY', 'N': 'KE', 'S': 'GI', 'G': 'KI', 'B': 'KA', 'R': 'HI', 'K': 'OU'}
        self.d6 = {v: k for k, v in self.d5.items()}

    def write_log(self, word):
        if self.log_file is not None:
            print(word, file=codecs.open(self.log_file, 'a', 'utf-8'))
        return

    def init_board(self):
        self.board = [['0'] * 9 for i in range(9)]
        self.board[0] = ['L', 'N', 'S', 'G', 'K', 'G', 'S', 'N', 'L']
        self.board[1] = ['0', 'R', '0', '0', '0', '0', '0', 'B', '0']
        self.board[2] = ['P'] * 9
        self.board[6] = ['P'] * 9
        self.board[7] = ['0', 'B', '0', '0', '0', '0', '0', 'R', '0']
        self.board[8] = ['L', 'N', 'S', 'G', 'K', 'G', 'S', 'N', 'L']
        return

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.keep_connect[0] = True
        self.keep_connect_thread = Thread(target=self.keep_connect_F)
        self.keep_connect_thread.start()
        return

    def keep_connect_F(self):
        time.sleep(10)
        while self.keep_connect[0]:
            if self.keep_connect[1]:
                time.sleep(10)
                continue
            self.send('')
            time.sleep(30)

    def send(self, mes):
        if len(mes) >= 1:
            w = '<csa_send> | ' + str(datetime.now()) + ' | ' + mes
            self.write_log(w)
        
        k = '\n'
        if k not in mes:
            mes += k
        self.socket.send(mes.encode('utf-8'))
        return

    def recv(self):
        mes = self.socket.recv(self.buf_size).decode('utf-8')
        if len(mes) > 1:
            w = '<csa_recv> | ' + str(datetime.now()) + ' | ' + mes
            self.write_log(w)
        return mes

    def recv_word(self, word):
        if type(word) == str:
            word = [word]
        while True:
            r = self.recv()
            for i in word:
                if i in r:
                    return r
        return

    def login(self, name, password):
        self.connect()
        self.send('LOGIN {} {}'.format(name, password))
        r = self.recv_word(['LOGIN'])
        if 'incorrect' in r:
            raise ValueError('LOGIN failed')
        self.keep_connect[1] = False
        return

    def logout(self):
        self.keep_connect[0] = False
        self.keep_connect_thread.join()
        time.sleep(3)
        self.send('LOGOUT')
        self.socket.close()
        return

    def wait(self):
        mes = self.recv_word(['Game_Summary'])
        return self.parse_summary(mes)

    def parse_summary(self, summary):
        lines = summary.splitlines()
        output = {'position': 'startpos moves', 'time': {'total': 0, 'inc': 0, 'byoyomi': 0},
                  'color': None, 'max_moves': None, 'player_name': [None, None]}
        for L in lines:
            if 'Your_Turn' in L:
                if '+' in L:
                    output['color'] = '+'
                else:
                    output['color'] = '-'
            if 'Max_Moves' in L:
                output['max_moves'] = int(L.split(':')[1])
            if 'Total_Time' in L:
                output['time']['total'] = int(L.split(':')[1])
            if 'Byoyomi' in L:
                output['time']['byoyomi'] = int(L.split(':')[1])
            if 'Increment' in L:
                output['time']['inc'] = int(L.split(':')[1])
            if 'Name+' in L:
                output['player_name'][0] = L.split(':')[1]
            if 'Name-' in L:
                output['player_name'][1] = L.split(':')[1]
        self.current_game_summary = output
        self.init_board()
        return output

    def agree(self):
        self.send('AGREE')
        r = self.recv_word(['START', 'REJECT'])
        if 'REJECT' in r:
            return False
        return True

    def csamove_to_index(self, csamove):
        index1 = [int(csamove[2])-1, 9-int(csamove[1])]
        index2 = [int(csamove[4])-1, 9-int(csamove[3])]
        return index1, index2

    def usimove_to_index(self, usimove):
        index1 = [int(self.d2[usimove[1]])-1, 9-int(usimove[0])]
        index2 = [int(self.d2[usimove[3]])-1, 9-int(usimove[2])]
        return index1, index2

    def board_push_csa(self, csamove):
        if csamove[1] + csamove[2] == '00':
            index = [int(csamove[4])-1, 9-int(csamove[3])]
            self.board[index[0]][index[1]] = self.d6[csamove[5] + csamove[6]]
            return
        index1, index2 = self.csamove_to_index(csamove)
        p = self.board[index1[0]][index1[1]]
        if csamove[5] + csamove[6] in ('TO', 'NY', '+l', 'NY', 'NK', 'NG', 'UM', 'RY') and p not in ('+P', '+L', '+N', '+S', '+B', '+R'):
            self.board[index2[0]][index2[1]] = '+' + p
        else:
            self.board[index2[0]][index2[1]] = p
        self.board[index1[0]][index1[1]] = '0'
        return

    def board_push_usi(self, usimove):
        if '*' in usimove:
            index = [int(self.d2[usimove[3]])-1, 9 - int(usimove[2])]
            self.board[index[0]][index[1]] = usimove[0]
            return
        index1, index2 = self.usimove_to_index(usimove)
        p = self.board[index1[0]][index1[1]]
        if '+' in usimove:
            self.board[index2[0]][index2[1]] = '+' + p
        else:
            self.board[index2[0]][index2[1]] = p
        self.board[index1[0]][index1[1]] = '0'
        return

    def send_move(self, usimove, comment=None):
        """
        usimove: str型。USIプロトコルのmove
        comment: オプション。評価値などを送れる

        返り値: 投了と勝ち宣言の場合はなし。それ以外は自分の手番で消費した時間( 単位は秒 )
        """
        if 'resign' in usimove:#投了
            self.toryo()
            return
        if 'win' in usimove:#勝ち宣言
            self.kachi()
            return
        if '*' in usimove:
            csamove =  self.current_game_summary['color'] + '00' + usimove[2] + self.d2[usimove[3]]
            csamove = csamove + self.d3[usimove[0]]
        else:
            csamove = self.current_game_summary['color'] + usimove[0] + self.d2[usimove[1]] + usimove[2] + self.d2[usimove[3]]
            index, _ = self.csamove_to_index(csamove)
            p = self.board[index[0]][index[1]]
            if '+' in usimove:
                csamove = csamove + self.d4['+' + p]
            else:
                csamove = csamove + self.d3[p]
        if comment is None:
            self.send(csamove)
        else:
            csamove_and_comment = csamove + ",'* " + str(comment)
            self.send(csamove_and_comment)
        self.board_push_csa(csamove)
        m, t = self.recv_move()
        if m == 'end':
            return
        return t

    def recv_move(self):
        end = ('#SENNICHITE', '#OUTE_SENNICHITE', '#ILLEGAL_MOVE', '#TIME_UP', '#RESIGN', '#JISHOGI',
               '#ILLEGAL_MOVE', '#MAX_MOVES', '#CHUDAN', '#WIN', '#DRAW', '#LOSE')
        r = self.recv_word(end + (',T',))
        for e in end:
            if e in r:
                return 'end', 0
        move = r.split(',')[0]
        if move[1] + move[2] == '00':
            usimove = self.d6[move[5] + move[6]] + '*' + move[3] + self.d1[move[4]]
            return usimove, int(r.split(',T')[1])
        
        usimove = move[1] + self.d1[move[2]] + move[3] + self.d1[move[4]]
        if move[5] + move[6] in ('TO', 'NY', 'NK', 'NG', 'UM', 'RY'):
            index, _ = self.csamove_to_index(move)
            if self.board[index[0]][index[1]] not in ('+P', '+p', '+L', '+l', '+N', '+n', '+S', '+s', '+B', '+b', '+R', '+r'):
                usimove = usimove + '+'
        return usimove, int(r.split(',T')[1])

    def toryo(self):
        self.send('%TORYO')
        self.recv_move()
        return

    def kachi(self):
        self.send('%KACHI')
        self.recv_move()
        return

    
