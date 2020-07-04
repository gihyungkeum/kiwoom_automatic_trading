## 66강. 프로그램으로 주식 주문넣고 체결 정보 받기


import os
import sys

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *

from config.kiwoomType import *


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print('Kiwoom 클래스 입니다')

        self.realType = RealType()

        ########### event loop 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()
        # ########################

        ######### 스크린 번호모음
        self.screen_number = '2000'
        self.screen_calculation_stock = '4000'
        self.screen_real_stock = '5000'
        self.screen_meme_stock = '6000'
        self.screen_start_stop_real = '1000'
        #################

        ########## 변수모음
        self.account_num = None
        # ##########################

        ######### 계좌관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5
        ################################

        ######### 딕셔너리 변수모음
        self.portfolio_stock_dict = {}
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.jango_dict = {}  # 2. jango_dict 빈객체 생성
        #############################

        #########  종목 분석용
        self.calcul_data = []
        #########################

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.not_concluded_account()

        self.read_code()
        self.screen_number_setting()

        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real, '',
                         self.realType.REALTYPE['장시작시간']['장운영구분'], '0')

        for code in self.portfolio_stock_dict.keys():
            screen_num = self.portfolio_stock_dict[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']

            self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, code, fids, '1')
            print('실시간 등록 코드 : %s, 스크린번호: %s, fid 번호: %s' % (code, screen_num, fids))

    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICTrl.1')

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)       #69_2 송수신 msg 수신할 이벤트 슬롯 추가

    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)

        self.OnReceiveChejanData.connect(
            self.chejan_slot)

    def signal_login_commConnect(self):
        self.dynamicCall('CommConnect()')

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def login_slot(self, errCode):
        # print(errCode)
        print(errors(errCode))

        self.login_event_loop.exit()

    def get_account_info(self):
        account_list = self.dynamicCall('GetLoginInfo(String)', 'ACCNO')
        self.account_num = account_list.split(';')[0]
        print('나의 보유계좌번호: %s' % self.account_num)

    def detail_account_info(self):
        print('예수금 요청하는 부분')

        self.dynamicCall('SetInputValue(String, String)', '계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)', '비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)', '비밀번호입력매체구분', '00')
        self.dynamicCall('SetInputValue(String, String)', '조회구분', '2')
        self.dynamicCall('CommRqData(String, String, String, String)', '예수금상세현황요청', 'opw00001', '0', self.screen_number)
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext='0'):
        print('계좌평가 잔고내역을 가져오는 부분 연속조회 %s ' % sPrevNext)

        self.dynamicCall('SetInputValue(String, String)', '계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(String, String)', '비밀번호', '0000')
        self.dynamicCall('SetInputValue(String, String)', '비밀번호입력매체구분', '00')
        self.dynamicCall('SetInputValue(String, String)', '조회구분', '2')
        self.dynamicCall('CommRqData(String, String, String, String)', '계좌평가잔고내역', 'opw00018', sPrevNext,
                         self.screen_number)
        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext='0'):
        print('미체결 요청')

        self.dynamicCall('SetInputValue(QString, QString)', '계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(QString, QString)', '체결구분', '1')
        self.dynamicCall('SetInputValue(QString, QString)', '매매구분', '0')
        self.dynamicCall('CommRqData(QString, QString, int, QString)', '실시간미체결요청', 'opt10075', sPrevNext,
                         self.screen_number)

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

        if sRQName == '예수금상세현황요청':
            deposit = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '예수금')
            print('예수금 %s 원' % deposit)

            self.use_money = int(deposit) * self.use_money_percent
            self.use_money = self.use_money / 4

            withdraw_amount = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0,
                                               '출금가능금액')

            print('출금가능금액 %s 원' % withdraw_amount)
            print('출금가능금액 형변환 %s 원' % int(withdraw_amount))

            self.detail_account_info_event_loop.exit()

        elif '주식일봉차트조회' == sRQName:
            # print('일봉데이터 요청')

            code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0, '종목코드')
            print('일봉데이터 요청 %s' % code)

        if sRQName == '계좌평가잔고내역':
            total_buy_money = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0, '총매입금액')
            total_buy_money_result = int(total_buy_money)
            print('총매입금액 %s 원' % total_buy_money_result)

            total_profit_loss_ratio = self.dynamicCall('GetCommData(String, String, int, String)', sTrCode, sRQName, 0,
                                                       '총수익률(%)')
            total_profit_loss_ratio_result = float(total_profit_loss_ratio)
            print('총수익률(%%) : %s' % total_profit_loss_ratio_result)

            rows = self.dynamicCall('GetRepeatCnt(QString, QString)', sTrCode, sRQName)

            cnt = 0
            for i in range(rows):
                code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목번호')

                code = code.strip()[1:]
                code_name = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목명')

                stock_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                  '보유수량')

                buy_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '매입가')

                learn_rate = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                              '수익률(%)')
                current_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                 '현재가')
                total_chegyul_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName,
                                                       i, '매입금액')
                possible_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                     '매매가능수량')

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code: {}})

                code_name = code_name.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegyul_price = int(total_chegyul_price.strip())
                possible_quantity = int(possible_quantity.strip())

                self.account_stock_dict[code].update({'종목명': code_name})
                self.account_stock_dict[code].update({'보유수량': stock_quantity})
                self.account_stock_dict[code].update({'매입가': buy_price})
                self.account_stock_dict[code].update({'수익률(%)': learn_rate})
                self.account_stock_dict[code].update({'현재가': current_price})
                self.account_stock_dict[code].update({'매입금액': total_chegyul_price})
                self.account_stock_dict[code].update({'매매가능수량': possible_quantity})

                cnt += 1

            print('계좌에 가지고 있는 종목 %s' % self.account_stock_dict)
            print('계좌보유종목 카운터 %s' % cnt)

            if sPrevNext == '2':
                self.detail_account_mystock(sPrevNext='2')
            else:
                self.detail_account_info_event_loop.exit()

        elif sRQName == '실시간미체결요청':
            rows = self.dynamicCall('GetRepeatCnt(QString, QString)', sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                        '종목코드')
                code_name = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '종목명')
                order_num = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '주문번호')
                order_status = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                '주문상태')
                order_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                  '주문수량')
                order_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                               '주문가격')
                order_gubun = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                               '주문구분')
                not_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                '미체결수량')
                ok_quantity = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                               '체결량')

                code = code.strip()
                code_name = code_name.strip()
                order_num = int(order_num.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_num in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_num] = {}

                self.not_account_stock_dict[order_num].update({'종목코드': code})
                self.not_account_stock_dict[order_num].update({'종목명': code_name})
                self.not_account_stock_dict[order_num].update({'주문번호': order_num})
                self.not_account_stock_dict[order_num].update({'주문상태': order_status})
                self.not_account_stock_dict[order_num].update({'주문수량': order_quantity})
                self.not_account_stock_dict[order_num].update({'주문가격': order_price})
                self.not_account_stock_dict[order_num].update({'주문구분': order_gubun})
                self.not_account_stock_dict[order_num].update({'미체결수량': not_quantity})
                self.not_account_stock_dict[order_num].update({'쳬결량': ok_quantity})

                print('미체결 종목: %s' % self.not_account_stock_dict[order_num])

            self.detail_account_info_event_loop.exit()

        elif '주식일봉차트조회' == sRQName:
            # print('일봉데이터 요청')

            # if sRQName = '주식일봉차트조회':

            code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0, '종목코드')

            code = code.strip()
            print('%s 일봉데이터 요청' % code)

            row_cnt = self.dynamicCall('GetRepeatCnt(QString, QString)', sTrCode, sRQName)
            print('데이터 일수 %s' % row_cnt)

            for i in range(row_cnt):
                data = []

                current_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                 '현재가')
                value = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '거래량')
                trading_value = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,
                                                 '거래대금')
                date = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '일자')
                start_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '시가')
                high_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '고가')
                low_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '저가')

                data.append('')
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append('')

                self.calcul_data.append(data.copy())

            # print(self.calcul_data)

            if sPrevNext == '2':
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                print('총일수 %s' % len(self.calcul_data))

                pass_success = False
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success = False
                else:
                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])

                    moving_average_price_120 = total_price / 120

                    bottom_stock_price = False
                    check_price = None

                    if int(self.calcul_data[0][7]) <= moving_average_price_120 and moving_average_price_120 <= int(
                            self.calcul_data[0][6]):
                        print('오늘 주가가 120일 이평선에 걸쳐있는 것을 확인')
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    prev_price = None
                    if bottom_stock_price == True:

                        moving_average_price_120_prev = 0
                        price_top_moving = False

                        idx = 1
                        while True:
                            if len(self.calcul_data[idx:]) < 120:
                                print('120일 치가 없음!')
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:120 + idx]:
                                total_price += int(value[1])
                            moving_average_price_120_prev = total_price / 120

                            if moving_average_price_120_prev <= int(self.calcul_data[idx][6]) and idx <= 20:

                                print('20일 동안 주가가 120 이편선과 같거나 위에 있으면 조건 통과 못함')
                                price_top_moving = False
                                break

                            elif int(self.calcul_data[idx][7]) > moving_average_price_120_prev and idx > 20:

                                print('20일이상 120일 이평선 위에 있는 일봉 확인됨')
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])
                                break

                            # else:
                            #     idx +=1

                            idx += 1

                        if price_top_moving == True:
                            if moving_average_price_120 > moving_average_price_120_prev and check_price > prev_price:
                                print('포착된 이편선의 가격이 오늘자(최근일자) 이평선 가격보다 낮은 것이 확인됨')
                                print('포착된 부분의 일봉 저가가 오늘자 일본의 고가보다 낮은지 확인됨')

                                pass_success = True

                if pass_success == True:
                    print('조건부 통과됨')

                    code_name = self.dynamicCall('GetMasterCodeName(QString)', code)

                    f = open('files/condition_stock.txt', 'a', encoding='utf8')
                    f.write('%s\t%s\t%s\n' % (code, code_name, str(self.calcul_data[0][1])))
                    f.close()

                elif pass_success == False:
                    print('조건부 통과 못함')

                self.calcul_data.clear()

                self.calculator_event_loop.exit()

    def get_code_list_by_market(self, market_code):
        '''
        종목코드를 반환
        :param market_code:
        :return:
        '''

        code_list = self.dynamicCall('GetCodeListByMarket(QString)', market_code)
        code_list = code_list.split(';')[:-1]
        return code_list

    def calculator_func(self):

        '''
        종목분석 실행용 함수   ....> #8. __init__ 함수 내에 임시용으로 실행할 함수 생성
        :return:
        '''

        code_list = self.get_code_list_by_market('10')
        print('코스닥 갯수 %s' % len(code_list))

        for idx, code in enumerate(code_list):
            self.dynamicCall('DisconnectRealData(QString)',
                             self.screen_calculation_stock)
            print('%s / %s : Kosdaq 종목코드 : %s 업데이팅' % (idx + 1, len(code_list), code))

            self.day_kiwoom_db(code=code)

    def day_kiwoom_db(self, code=None, date=None, sPrevNext='0'):

        QTest.qWait(3600)

        self.dynamicCall('SetInputValue(QString, QString)', '종목코드', code)
        self.dynamicCall('SetInputValue(QString, QString)', '수정주가구분', '1')

        if date != None:
            self.dynamicCall('SetInputValue(QString, QString)', '기준일자', date)

        self.dynamicCall('CommRqData(QString, QString, int, QString)', '주식일봉차트조회', 'opt10081', sPrevNext,
                         self.screen_calculation_stock)

        self.calculator_event_loop.exec_()

    def read_code(self):
        if os.path.exists('files/condition_stock.txt'):
            f = open('files/condition_stock.txt', 'r', encoding='utf8')
            lines = f.readlines()
            for line in lines:
                if line != '':
                    ls = line.split('\t')

                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(
                        ls[2].split('\n')[0])
                    stock_price = abs(stock_price)

                    self.portfolio_stock_dict.update(
                        {stock_code: {'종목명': stock_name, '현재가': stock_price}})

            f.close()

            print(self.portfolio_stock_dict)

    def screen_number_setting(self):
        screen_overwrite = []

        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]['종목코드']

            if code not in screen_overwrite:
                screen_overwrite.append(code)

        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        cnt = 0
        for code in screen_overwrite:

            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({'스크린번호': str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({'주문용스크린번호': str(self.screen_meme_stock)})

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update(
                    {code: {'스크린번호': str(self.screen_real_stock), '주문용스크린번호': str(self.screen_meme_stock)}})

            cnt += 1

        print(self.portfolio_stock_dict)

    def realdata_slot(self, sCode, sRealType, sRealData):
        '''
        OnReceiveRealData(
          BSTR sCode,        // 종목코드
          BSTR sRealType,    // 리얼타입
          BSTR sRealData    // 실시간 데이터 전문
          )
        :return:
        '''

        # print(sCode)

        if sRealType == '장시작시간':
            fid = self.realType.REALTYPE[sRealType]['장운영구분분']
            value = self.dynamicCall('GetCommRealData(QString, int)', sCode, fid)

            if value == '0':
                print('장 시작 전')

            elif value == '3':
                print('장 시작')

            elif value == '2':
                print('장 종료, 동시호가로 넘어감')

            elif value == '4':
                print('3시30분 장 종료')


                #69_4 파일삭제함수 호출 및 종목계산 함수 호출... 추가로 지원보고자 하는 것을 추가로 작성하고 시험해 봄

                for code in self.portfolio_stock_dict.keys():      #69_4_3
                    self.dynamicCall('SetRealRemove(QString, QString)', self.portfolio_stock_dict[sCode]['스크린번호'], sCode)

                QTest.qWait(5000)                  #69_4_4


                self.file_delete()    #69_4_1
                self.calculator_func()    #69_4_2

                sys.exit() # 69_4_5

        elif sRealType == '주식체결':
            # print(sCode)

            a = self.dynamicCall('GetCommRealData(QString, int)', sCode,
                                 self.realType.REALTYPE[sRealType]['체결시간'])
            b = self.dynamicCall('GetCommRealData(QString, int)', sCode,
                                 self.realType.REALTYPE[sRealType]['현재가'])
            b = abs(int(b))

            c = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['전일대비'])
            c = abs(int(c))

            d = self.dynamicCall('GetCommRealData(QString, int)', sCode,
                                 self.realType.REALTYPE[sRealType]['등락율'])
            d = float(d)

            e = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['(최우선)매도호가'])
            e = abs(int(e))

            f = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['(최우선)매수호가'])
            f = abs(int(f))

            g = self.dynamicCall('GetCommRealData(QString, int)', sCode,
                                 self.realType.REALTYPE[sRealType]['거래량'])
            g = abs(int(g))

            h = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['누적거래량'])
            h = abs(int(h))

            i = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['고가'])
            i = abs(int(i))

            j = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['시가'])
            j = abs(int(j))

            k = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['저가'])
            k = abs(int(k))

            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode: {}})

            self.portfolio_stock_dict[sCode].update({'체결시간': a})
            self.portfolio_stock_dict[sCode].update({'현재가': b})
            self.portfolio_stock_dict[sCode].update({'전일대비': c})
            self.portfolio_stock_dict[sCode].update({'등락율': d})
            self.portfolio_stock_dict[sCode].update({'(최우선)매도호가': e})
            self.portfolio_stock_dict[sCode].update({'(최우선)매수호가': f})
            self.portfolio_stock_dict[sCode].update({'거래량': g})
            self.portfolio_stock_dict[sCode].update({'누적거래량': h})
            self.portfolio_stock_dict[sCode].update({'고가': i})
            self.portfolio_stock_dict[sCode].update({'시가': j})
            self.portfolio_stock_dict[sCode].update({'저가': k})

            print(self.portfolio_stock_dict[sCode])

            # 계좌장고 평가내역에 있고 오늘 산 잔고에는 없는 경우
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():  # 1. 실시간으로 데이터 받은 후, 매도 /매수 결정을 위한 조건문 작성. jango_dict는 오늘 산 것
                # print('%s %s' % ('신규매도를 한다', sCode))

                asd = self.account_stock_dict[sCode]

                # 11. 65강 조건에 맞으면 자동으로 주문 넣기
                meme_rate = (b - asd['매입가']) / asd['매입가'] * 100

                if asd['매매가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                    order_success = self.dynamicCall(
                        'SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
                        ['신규매도', self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 2,
                        sCode, asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ''])            #8.데이터를 리스트로 묶어줌

                    if order_success == 0:
                        print('매도주문 전달성공')
                        del self.account_stock_dict[sCode]
                    else:
                        print('매도주문 전달 실패')


            # 오늘 산 잔고에 있을 경우
            elif sCode in self.jango_dict.keys():

        #13. 68강 주문요청마무리.
        #         print('%s %s' % ('신규매도를 한다2', sCode))

                jd = self.jango_dict[sCode]
                meme_rate = (b - jd['매입단가']) / jd['매입단가'] * 100     #14. b---현재가

                if jd['주문가능수량'] > 0 and (meme_rate>5 or meme_rate <-5):

                    order_success = self.dynamicCall(
                    'SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
                    ['신규매도', self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 2,
                     sCode, jd['주문가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ''])  # 8.데이터를 리스트로 묶어줌

                if order_success == 0:
                    self.logging.logger.debug('매도주문 전달 성공')
                    # del self.account_stock_dict[sCode]     #14. 라인801 코드로 제거해 주었기에 del 불필요--self.dynamicCall('SetRealRemove(QString, QString)', self.portfolio_stock_dict[sCode]['스크린번호'], sCode)

                else:
                    self.logging.logger.debug('매도주문 전달 실패')


            # 등락율이 2.0% 이상이고 오늘 산 잔고에 없을 경우
            elif d > 2.0 and sCode not in self.jango_dict:  # 2. d -->등락율
                print('%s %s' % ('신규매수를 한다', sCode))

                result = (self.use_money * 0.1) / e   #15. e---현재가(?)
                quantity = int(result)

                order_success = self.dynamicCall(
                    'SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
                    ['신규매수', self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 1,
                     sCode, quantity, e, self.realType.SENDTYPE['거래구분']['지정가'], ''])

                if order_success == 0:
                    self.logging.logger.debug('매수주문 전달 성공')

                else:
                    self.logging.logger.debug('매수주문 전달 실패')


            not_meme_list = list(self.not_account_stock_dict)

            for order_num in not_meme_list:
                code = self.not_account_stock_dict[order_num]['종목코드']
                meme_price = self.not_account_stock_dict[order_num]['주문가격']
                not_quantity = self.not_account_stock_dict[order_num]['미체결수량']
                # meme_gubun = self.not_account_stock_dict[order_num]['매도수구분']

                order_gubun = self.not_account_stock_dict[order_num]['주문구분']   #8. 매도수구분 지우고 대신 주문구분으로


                # if meme_gubun == '매수' and not_quantity > 0 and e > meme_price:  #8-1.. 지우고
                if order_gubun == '매수' and not_quantity > 0 and e > meme_price:     #8-2,  주문구분(order_gubun)으로

                    # print('%s %s' % ('매수취소 한다', sCode))

                    #16. 매수취소
                    order_success = self.dynamicCall(
                        'SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
                        ['매수취소', self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 3,      #17.  3--매수취소, 0--전량취소
                         code, 0, 0, self.realType.SENDTYPE['거래구분']['지정가'], order_num])                     #18. order_num--djEjs 어떤 주문을 취소 할 것이냐를 명시

                    if order_success == 0:                                                                #19
                        self.logging.logger.debug('매수주문 전달 성공')

                    else:
                        self.logging.logger.debug('매수주문 전달 실패')



                elif not_quantity == 0:
                    del self.not_account_stock_dict[order_num]

    def chejan_slot(self, sGubun, nItemCnt, sFIdList):  # 6. chejan_slot()함수생성


        if int(sGubun) == 0:  # 7. sGubun 값이 스트링으로나와서 정수로 형변화
            # print('주문체결')

            account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목코드'])[1:]

            stock_name = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()

            origin_order_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['원주문번호'])  #1. 처음 신규주문은 원주문번호가 없음. default : '000000'
            order_number = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문번호'])

            order_status = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문상태'])
            order_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)

            order_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문가격'])
            order_price = int(order_price)

            not_chegual_quan =  self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['미체결수량'])
            not_chegual_quan = int(not_chegual_quan)

            order_gubun = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문구분'])
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            # meme_gubun = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['매도수구분']) #2. 매수: 2, 매도:1
            # meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]    #3. 매도/매수 2가지만 나오므로 보기좋게 한글로 바꾸어준것

            chegual_time_str =  self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['주문/체결시간'])

            chegual_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결가'])

            if chegual_price == '':   #4. 처음에 주문넣으면 접수 상태이므로 체결가 없음 따라서 빈값.
                chegual_price = 0

            else:
                chegual_price = int(chegual_price)

            chegual_quantity = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['체결량'])  #5. 출력: default = ''

            if chegual_quantity == '':
                chegual_quantity = 0

            else:
                chegual_quantity = int(chegual_quantity)

            current_price =  self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['현재가'])
            current_price = abs(int(current_price))

            first_sell_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price =  self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['주문체결']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))


            if order_number not in self.not_account_stock_dict.keys(): #6. 새로 들어온 주문이면 주분번호 할당. 딕셔너리 업데이트
                self.not_account_stock_dict.update({order_number: {}})

            #7. 데이타를 딕셔너리에 넣어줌

            self.not_account_stock_dict[order_number].update({'종목코드': sCode})
            self.not_account_stock_dict[order_number].update({'주문번호': order_number})
            self.not_account_stock_dict[order_number].update({'종목명':stock_name})
            self.not_account_stock_dict[order_number].update({'주문상태':order_status})
            self.not_account_stock_dict[order_number].update({'주문수량': order_quan})
            self.not_account_stock_dict[order_number].update({'주문가격':order_price})
            self.not_account_stock_dict[order_number].update({'미체결수량':not_chegual_quan})
            self.not_account_stock_dict[order_number].update({'원주문번호':origin_order_num})
            self.not_account_stock_dict[order_number].update({'주문구분':order_gubun})
            # self.not_account_stock_dict[order_number].update({'매도수구분':meme_gubun})
            self.not_account_stock_dict[order_number].update({'주문/체결시간':chegual_time_str})
            self.not_account_stock_dict[order_number].update({'체결가':chegual_price})
            self.not_account_stock_dict[order_number].update({'체결량':chegual_quantity})
            self.not_account_stock_dict[order_number].update({'현재가':current_price})
            self.not_account_stock_dict[order_number].update({'(최우선)매도호가':first_sell_price})
            self.not_account_stock_dict[order_number].update({'(최우선)매수호가가':first_buy_price})

            # print(self.not_account_stock_dict)


        elif int(sGubun) == 1:
            # print('잔고')  # kao>실시간>잔고, 주문체결


            #9. 잔고 데이타 정리
            account_num = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)

            buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = int(buy_price)

            total_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['총매입가'])
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['매도/매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall('GetChejanData(int)', self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))


            #10. 잔고 데이터를 딕셔너리에 넣어줌

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})   #11. 업데이트

            self.jango_dict[sCode].update({'현재가': current_price})
            self.jango_dict[sCode].update({'종목코드': sCode})
            self.jango_dict[sCode].update({'종목명': stock_name})
            self.jango_dict[sCode].update({'보유수량': stock_quan})
            self.jango_dict[sCode].update({'주문가능수량': like_quan})
            self.jango_dict[sCode].update({'매입단가': buy_price})
            self.jango_dict[sCode].update({'총매입가': total_buy_price})
            self.jango_dict[sCode].update({'매도/매수구분': meme_gubun})
            self.jango_dict[sCode].update({'(최우선)매도호가': first_sell_price})
            self.jango_dict[sCode].update({'(최우선)매수호가': first_buy_price})

            #12. 잔고가 없으면 디셔너리에서 삭제하고, 해당 종목과 연결을 끊어줌

            if stock_quan == 0:
                del self.jango_dict[sCode]
                self.dynamicCall('SetRealRemove(QString, QString)', self.portfolio_stock_dict[sCode]['스크린번호'], sCode)


    #69강 주식장 종료후 마무리 작업

    ##69-1 송수신 메세지 get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        print('스크린: %s, 요청이름:%s, tr코드: %s --- %s' %(sScrNo, sRQName, sTrCode, msg))


    #69_3 장이 마감하면 다음날을 위하여, 파일을 분석하고 저장한 파일을 지우고(files>condition_stock.txt)를 다시 만드는 것이 좋음.

    #69_3 파일 삭제

    def file_delete(self):
        if os.path.isfile('files/condition_stock.txt'):
            os.remove('files/condition_stock.txt')






