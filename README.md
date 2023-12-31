# Ari_Shogi-Server-Client
USIエンジンがshogi-serverに接続して対局するためのプログラム

# 概要
- 数日前、あるプログラムの一部としてUSIエンジンをshogi-serverで対局させるためのプログラムを作った。そのプログラムを公開しようと思ったので少しだけ調整した。そしてできたものがこれ。
- コードが汚い、動作が遅い、そして不安定。
- USIプロトコルに関しては http://shogidokoro.starfree.jp/usi.html 、CSAプロトコルに関しては http://www2.computer-shogi.org/protocol/tcp_ip_server_121.html を参考。
- floodgateの http://wdoor.c.u-tokyo.ac.jp/shogi/view/show-player.cgi?event=LATEST&filter=floodgate&show_self_play=1&user=Li_with_Ari_Shogi-Server-Client%2Bfa6250961bd946dd412a36857953dea2 のアカウントで動作チェック中。(2023/07/18)

# 機能
- USIエンジンをCSAプロトコルで動くサーバー( floodgateとか )で対局させられる。
- USIエンジンのオプションも設定できる。
- USIエンジンのPonderも使える。
- 評価値を送れる。(読み筋は不可)
- ブラックリストに登録してある対局相手と当たった場合はリジェクトできる。
- 望んだ手番ではなかった場合、リジェクトできる。
- ログをとれる。本体 / CSAプロトコルでの通信 / USIプロトコルでの通信、の3種類。
- 次の対局開始時刻が近づいている時、自分の評価値が一定以下の場合に投了する機能。(floodgateで使うことを想定した機能。将棋AI開発者の誰かがしばらく前に「こんな機能があったら良いな」と何処かで言っていた気がする)

# 今後追加するかもしれない機能
- 指定局面開始
- 設定ファイルに設定を保存する機能。設定ファイルから設定を読み込む機能。
- 読み筋を送る機能

# 引数
## 必須のもの
- engine_path: USIエンジンのpath。
- login_name: サーバーにログインする際の名前。
- password: サーバーにログインする際のパスワード。floodgateで普通に対局したいなら'floodgate-300-10F,{好きなパスワード}'という感じにする必要がある。(例: 'floodgate-300-10F,0000')

## オプション
- --engine_options: USIエンジンのオプション。{オプション名}:{設定値},{オプション名}:{設定値}・・・、という感じに設定する。(例: USI_Ponder:false,USI_Hash:256,EvalDir:aaaa/aaa)
- --use_ponder: USIエンジンのPonder( 相手番にも思考する機能 )を使用するかどうかのオプション。デフォルトOFF。--use_ponderと引数に入れて起動した時のみ有効になる。
- --server: 接続先。デフォルトではfloodgate( http://wdoor.c.u-tokyo.ac.jp/shogi/floodgate.html )
- --port: ポート。デフォルト4081。基本的に4081以外は使わない。
- --games: 対局数。デフォルト1。リジェクトした対局もカウントする。
- --log_file: 本体のログ。デフォルトでは無し。
- --log_file_csa: CSAプロトコルでの通信に関するログ。デフォルトでは無し。
- --log_file_usi: USIプロトコルでの通信に関するログ。デフォルトでは無し。
- --blacklist: ブラックリスト。デフォルトでは空。拒否したい相手の名前を','で区切って記入する。(例: KirainaYatsu1,KiranaYatsu2,DaikirainaYatsu)
- --play_black_only: 先手番でのみ対局したいときのオプション。--play_black_onlyと引数に入れて起動した時のみ有効になる。マッチングした際、自分が後手番だとリジェクトする。
- --play_white_only: 後手番でのみ対局したいときのオプション。--play_white_onlyと引数に入れて起動した時のみ有効になる。マッチングした際、自分が先手番だとリジェクトする。
- --time_aware_toryo: 現在時刻と評価値が条件を満たした場合に投了する機能。デフォルトでは無し。{分}_{評価値}という感じで設定。(例: 5_300 => 次の対局開始まで残り5分を切って、かつ自分の評価値が-300以下の場合、投了する。)

# 使用例
```
python -m main AriShogi.bat AriShogiTest floodgate-300-10F,0123 --engine_options USI_Ponder:false,USI_Hash:4096,Threads:4,BookFile:no_book --games 20 --log_file main_log.txt --log_file_csa csa_log.txt --log_file_usi usi_log.txt --time_aware_toryo 10_1000 --blacklist KirainaYatsu1,KiranaYatsu2,DaikirainaYatsu --play_black_only
```

# ライセンス
- MITライセンス。詳細はLICENSEファイルを確認してください。
