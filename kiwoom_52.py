##### https://joytk.tistory.com/19
#### Failed calling sys.__interactivehook__
###### line 82  for line in open (filename, 'r') ---> (filename, 'r', encoding = 'utf-8')




from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *                     #5. tr요청 에러 방지를 위한 시간조정


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print('Kiwoom 클래스 입니다')

        ########### event loop 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop=QEventLoop()            # 3. day_kiwoom.db함수의 결과를 위한 이벤트루프 새로 생성. 물론 위에것 하나로 모두 사용하여도 상관없음
        # ########################

        ######### 스크린 번호모음
        self.screen_number = '2000'
        self.screen_calculation_stock = '4000'
        #################


        ########## 변수모음
        self.account_num = None
        # ##########################

        ######### 계좌관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5
        ################################

        ######### 딕셔너리 변수모음
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        #############################

        #########  종목 분석용
        self.calcul_data =[]                      #12.
        #########################

        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.not_concluded_account()

        self.calculator_func()

    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICTrl.1')

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

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
        print('계좌평가 잔고내역을 가져오는 부분 연속조회 %s ' %sPrevNext)

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
        self.dynamicCall('CommRqData(QString, QString, int, QString)', '실시간미체결요청', 'opt10075', sPrevNext, self.screen_number)

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

            code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0,
                                    '종목코드')  #1. KAO>TR>주식일봉차트조회>싱글데이터>종목코드

            print('일봉데이터 요청 %s' %code)

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
                                        '종목번호')
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

        elif '주식일봉차트조회' == sRQName:    ##52강에서 아래처럼 함수 변경함
            # print('일봉데이터 요청')

        # if sRQName = '주식일봉차트조회':

            code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0,'종목코드')
                              #1. 종목코드 가져오기 --싱글데이터 종목코드로 int자리 i --> 1, QString --> '종목코드'
            code = code.strip()     #6. 코드내 불필요 빈공간 제거
            print('%s 일봉데이터 요청' % code)   #2. 실행하면 --에러 발생됨--> 이벤트 루프로 블록 처리 필요

            row_cnt = self.dynamicCall('GetRepeatCnt(QString, QString)', sTrCode, sRQName)
            print('데이터 일수 %s' % row_cnt)       #7. 몇일치를 받아올 수 있는지 카운팅

            # GetCommDataEx() 함수로 for문을 돌리면 600개 리스트가 아래형식처럼 나옴. 이형식에맞쳐주기 위하여 #10, 10-1과 같이 빈리스트 인자 만들어줌
            # data = self.dynamicCall('GetCommDataEx(QString, QString)', sTrCode, sRQName)
            # [['', '현재가', '거래량','거래대금','날자', '시가', '고가', '저가', '' ], ['','현재가','거래량','거래대금',....,'']]

            # 8. 한번에 600일치까지 조회가능. KOA>TR주식일봉차트조회> 003000..1>조회
            for i in range(row_cnt):  #9. 상장일 이후 부터 일봉데이타를 리스트로 담아놓고 조건부 계산
                data = []

                current_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i,'현재가')
                value = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '거래량')
                trading_value = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '거래대금')
                date = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '일자')
                start_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '시가')
                high_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '고가')
                low_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '저가')

                data.append('')      #10. 데이타를 담아둘 빈 data 생성
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append('')                  #10-1.

                self.calcul_data.append(data.copy())     #11.  에러난 경우 self.calcul_data.append(data) Q&A에서

            # print(self.calcul_data)



            if sPrevNext == '2':          #4.  종목코드에 과거 데이타가 있으면 sPrevNext='2' 이면 다시요청한다
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                print('총일수 %s' % len(self.calcul_data))

                # 13. 120일 이평선 그릴만큼 데이터가 있는지 체크

                pass_success = False
                if self.calcul_data == None or len(self.calcul_data) < 120:   #12 조건문
                    pass_success = False
                else:
                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])  # 14. value[1] -- 라인 283(라인 268) 즉 120일치 현재가 합

                    moving_average_price_120 = total_price / 120   #15 오늘기준 120일 종가의 평균가

                    if int(self.calcul_data[0][7]) <= moving_average_price_120  and moving_average_price_120 <= int(self.calcul_data[0][6]):
                        #16. calcul_data[0][7] --> 오늘자[0] 저가[7]가 120 이평선과 같거나 낮은 경우, 그리고 calsul_data[0][6] -->  오늘자[0] 고가[6]가 이평선 보다 높거나 같은경우
                        #16: 즉 오늘자 가격대가  120일 이평선에 걸쳐있는 경우를 의미
                        print('오늘 주가가 120일 이평선에 걸쳐있는 것을 확인')

                self.calculator_event_loop.exit() #5. 앞에것을 요청하는 동안 다음것이 실행됮 않도록 이벤트루트를 끊어줌

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

        QTest.qWait(3600)    # 이벤트진행과 네트워크 진행이 살아있는 상태에서 다음코드의 진행을 3.6초 연기하여 진행되도록

        self.dynamicCall('SetInputValue(QString, QString)', '종목코드', code)
        self.dynamicCall('SetInputValue(QString, QString)', '수정주가구분', '1')

        if date != None:
            self.dynamicCall('SetInputValue(QString, QString)', '기준일자', date)

        self.dynamicCall('CommRqData(QString, QString, int, QString)', '주식일봉차트조회', 'opt10081', sPrevNext,
                         self.screen_calculation_stock)

        self.calculator_event_loop.exec_()     #3.TR요청하는 동안 다른 코드들이 실행되지 않도록 블록쳐주어야 함.
                                            # for문 사용으로..첫번째 종목요청후 종료가 되지 않은 상태에서 바로 두번째 종목 요청되는 것 방지필요
