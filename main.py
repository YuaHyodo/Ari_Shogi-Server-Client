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

from USI import Engine
from CSA import Client
import codecs
import argparse
from datetime import datetime

class Online:
    def __init__(self, engine, opt, use_ponder, player, host, port, main_log='none',
                 csa_log='none', usi_log='none', Blist=[], play_only_color=[False, False],
                 time_aware_toryo=None):
        self.engine_path = engine
        self.client = Client(host, port=port, log_file=csa_log if csa_log != 'none' else None)
        self.player = player
        self.opt = opt
        self.use_ponder = use_ponder
        
        self.log_file = main_log if main_log != 'none' else None
        self.usi_log = usi_log if usi_log != 'none' else None

        self.blacklist = Blist
        self.play_black_only = play_only_color[0]
        self.play_white_only = play_only_color[1]

        self.time_aware_toryo = time_aware_toryo
        if self.time_aware_toryo is not None:
            self.time_aware_toryo = [int(i) for i in self.time_aware_toryo.split('_')]
            self.time_aware_toryo[1] = self.time_aware_toryo[1] * -1

        self.write_log('engine: {}, engine_options: {}, host: {}, port: {}, login_name: {}, password: {}, main_log_file: {}, csa_log_file: {}, usi_log_file: {}, blacklist: {}, play_only_color: {}'.format(engine, opt,
                            host, port, player[0], player[1], main_log, csa_log, usi_log, Blist, play_only_color))

    def write_log(self, word):
        w = str(datetime.now()) + ' | ' + word
        print(w, file=codecs.open(self.log_file, 'a', 'utf-8'))
        return

    def setup_engine(self):
        self.write_log('setup_engine')
        self.engine = Engine(self.engine_path, log_file=self.usi_log)
        for k, v in self.opt.items():
            self.engine.setoption(k, v)
        self.engine.newgame()
        return

    def stop_engine(self):
        self.write_log('stop_engine')
        self.engine.stop()
        return

    def TimeAwareToryo(self, score):
        if score is None or self.time_aware_toryo is None:
            return False
        now = datetime.now()
        if now.minute >= 30:
            #30分～59分
            if 60 - self.time_aware_toryo[0] > now.minute:
                return False
            if score <= self.time_aware_toryo[1]:
                self.write_log('time_aware_toryo / score={} / {} / {}'.format(score, now.minute, self.time_aware_toryo))
                return True
        else:
            #0分～29分
            if 30 - self.time_aware_toryo[0] > now.minute:
                return False
            if score <= self.time_aware_toryo[1]:
                self.write_log('time_aware_toryo / score={} / {} / {}'.format(score, now.minute, self.time_aware_toryo))
                return True
        return False

    def game(self, games):
        for game_num in range(games):
            self.write_log('game: {} / {}'.format(game_num+1, games))
            #try:
            if True:  
                self.setup_engine()
                self.client.login(self.player[0], self.player[1])
                self.client.keep_connect[1] = False
                summary = self.client.wait()
                self.write_log('get gamesummary: {}'.format(summary))
                reject = False
                for i in range(len(self.blacklist)):
                    if self.blacklist[i] in summary['player_name']:
                        self.write_log('reject / {} in blacklist'.format(self.blacklist[i]))
                        self.client.send('REJECT')
                        reject = True
                        break
                if summary['color'] == '+' and self.play_white_only:
                    self.write_log('reject / play_white_only == true / mycolor == Black')
                    self.client.send('REJECT')
                    reject = True
                if summary['color'] == '-' and self.play_black_only:
                    self.write_log('reject / play_black_only == true / mycolor == White')
                    self.client.send('REJECT')
                    reject = True
                    break
                if not reject:
                    reject = not self.client.agree()
                if reject:#リジェクトした or された
                    self.write_log('reject')
                    self.client.logout()
                    self.stop_engine()
                    continue
                self.write_log('start game')
                self.client.keep_connect[1] = True
                pondermove = None#pondermoveを返さなかった場合や、設定でponderを使わない場合はNone
                #以下、対局
                if summary['color'] == '+':
                    #初手
                    self.engine.send('position ' + summary['position'])
                    self.engine.send('go btime {} wtime {} binc {} winc {} byoyomi {}'.format(summary['time']['total'] * 1000,
                        summary['time']['total'] * 1000, summary['time']['inc'] * 1000,
                        summary['time']['inc'] * 1000, summary['time']['byoyomi'] * 1000))
                    move, pondermove, score = self.engine.get_move(score=True, ponder=self.use_ponder)
                    summary['position'] = summary['position'] + ' ' + move
                    t = self.client.send_move(move, comment=score)
                    if self.use_ponder and pondermove is not None:
                        #ponderを使用する設定がON and エンジンがpondermoveを返した
                        self.engine.send('position ' + summary['position'] + ' ' + pondermove)
                        self.engine.send('go ponder')
                    """
                    CSAプロトコルでは「加算時間は自分の手番が来た時に加算される」となっている様だが、
                    加算した後の時間をエンジンに送ると2回加算される( 残り時間8秒、加算10秒とすると、
                    こちら側と向こう側で10秒ずつ足されてしまい、本来なら18秒以上思考すると切れ負けになるのに
                    28秒まで思考しても大丈夫だと解釈される)ので、加算時間を処理する部分を変更した。
                    (以前の方式のまま、エンジン側に加算時間の情報を送らないようにする事でも対処できると思う)
                    """
                    summary['time']['total'] += summary['time']['inc']
                    summary['time']['total'] -= t
                while True:
                    opponent_move, _ = self.client.recv_move()
                    if opponent_move == 'end':
                        break
                    self.client.board_push_usi(opponent_move)
                    summary['position'] = summary['position'] + ' ' + opponent_move    
                    if self.use_ponder and pondermove is not None:
                        if opponent_move == pondermove:
                            #ponderhit
                            self.engine.send('ponderhit')
                        else:
                            #外れた場合、stopコマンドで停止させた後、通常通りの思考を行う
                            self.engine.send('stop')
                            #stopコマンドで正常に停止した場合はbestmoveが来るので、それが来るまで待機
                            self.engine.get_move(score=False, ponder=False)
                    if not self.use_ponder or pondermove is None or opponent_move != pondermove:
                        #ponderを使用する設定がOFF
                        #or エンジンがpondermoveを返さなかった
                        #or pondermoveが外れた場合の処理
                        self.engine.send('position ' + summary['position'])
                        self.engine.send('go btime {} wtime {} binc {} winc {} byoyomi {}'.format(summary['time']['total'] * 1000,
                            summary['time']['total'] * 1000, summary['time']['inc'] * 1000,
                            summary['time']['inc'] * 1000, summary['time']['byoyomi'] * 1000))
                    move, pondermove, score = self.engine.get_move(score=True, ponder=self.use_ponder)
                    if self.TimeAwareToryo(score):
                        self.client.toryo()
                        break
                    summary['position'] = summary['position'] + ' ' + move
                    if summary['color'] == '-' and score is not None:
                        score *= -1
                    t = self.client.send_move(move, comment=score)
                    if t is None:
                        break
                    if self.use_ponder and pondermove is not None:
                        self.engine.send('position ' + summary['position'] + ' ' + pondermove)
                        self.engine.send('go ponder')
                    summary['time']['total'] += summary['time']['inc']
                    summary['time']['total'] -= t
                self.write_log('game finish')
                self.client.keep_connect[1] = False
                self.write_log('logout')
                self.client.logout()
                self.stop_engine()
            #except:
            else:
                self.write_log('error')
                time.sleep(10)
        return

p = argparse.ArgumentParser()
p.add_argument('engine_path', type=str)
p.add_argument('login_name', type=str)
p.add_argument('password', type=str)
p.add_argument('--engine_options', type=str, default='')
p.add_argument('--use_ponder', action='store_true')

p.add_argument('--server', type=str, default='wdoor.c.u-tokyo.ac.jp')
p.add_argument('--port', type=int, default=4081)
p.add_argument('--games', type=int, default=1)

p.add_argument('--log_file', type=str, default='none')
p.add_argument('--log_file_csa', type=str, default='none')
p.add_argument('--log_file_usi', type=str, default='none')

p.add_argument('--blacklist', type=str, default='')
p.add_argument('--play_black_only', action='store_true')
p.add_argument('--play_white_only', action='store_true')

p.add_argument('--time_aware_toryo', type=str, default='')
args = p.parse_args()

if args.engine_options.split(',')[0] != '':
    opt = {i.split(':')[0]: i.split(':')[1] for i in args.engine_options.split(',')}
else:
    opt = {}

player = [args.login_name, args.password]

Blist = [i for i in args.blacklist.split(',') if len(i) >= 2]

time_aware_toryo = args.time_aware_toryo if '_' in args.time_aware_toryo else None

online = Online(args.engine_path, opt, args.use_ponder, player, args.server, args.port, main_log=args.log_file,
                Blist=Blist, play_only_color=[args.play_black_only, args.play_white_only],
                csa_log=args.log_file_csa, usi_log=args.log_file_usi,
                time_aware_toryo=time_aware_toryo)
online.game(args.games)
