## 59강.  주식종목 수천개 ㅂ실시간 파일종목 읽기, 종목별 스크린번호 할당하기

import os  # 5. os 임포트

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *

from config.kiwoomType import *     #6. kiwoomType.py 임포트


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print('Kiwoom 클래스 입니다')

        self.realType = RealType()  #7. RealType클래스 객체화후 인스던스에 바인딩

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
        self.screen_start_stop_real = '1000'   #5 장상태를 알기위한 스크린번호를 변수로 저장
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
        #############################

        #########  종목 분석용
        self.calcul_data = []
        #########################

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()    # 16. 실시간 이벤트 슬롯 실행함수

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.not_concluded_account()


        self.read_code()
        self.screen_number_setting()


        #3. 실시간 등록을 위한 시그널 구성 _ 실시간 등록 함수: kao>개발자도구>조건검색>SetRealReg()
        #4. 실시간 데이터 받기 위해서 장 상태(시작, 끝, 장외..)를 받아야함. 이를 위하여 다음같이 코딩

        self.dynamicCall('SetRealReg(QString, QString, QString, QString)', self.screen_start_stop_real,'', self.realType.REALTYPE['장시작시간']['장운영구분'],'0' )

        #5. 화면번호 변수, 종목코드는 빈값으로 - 장 상태 확인만 하면 되니까,
        ## FID 번호 --  kao>실시간목록>장시작시간..종목코드 빈값으로 보내면 장 시작, 장외 등을 알 수 있음. Real Type를 보내면
        # 이름이 그대로 실시간 슬롯으로 나옴. 따라서 라인510 realdata_slot(self, sCode, sRealType, sRealData)에 보면 sRealType에
        # (한글)명이 나오는 것임. 이름이 나왔으면 꺼내 오기위하여 getCommRealData()를 사용하는데, 이때 사용되는 것이
        # 앞에번호[215], [20]. [214] 가 FID번호. FID번호는 장시작 항목뿐 아니라, 다른곳에도 같은 번호가 있으면 해당 데이타도 함께 가져옴.
        # 또한 장 시작전에 215를 등록 하였으면, 받을 때는 215, 20, 214 모두 나옴. 이런상태에서 우리는 원하는 것만 꺼내서 쓰면 됨.


        #8. self.realType.REALTYPE ->리얼타입에 접근후 첫 딕셔너리는['장시작시간'] 두번째는 ['장운영구분'] -> 215가 꺼내짐
        #9. '0' -> 최초등록, 그이후 실시간으로 볼게 있다하면 '1'로 추가등록 해야함. 이때 '0'으로하면 초기화됨

        for code in self.portfolio_stock_dict.keys():  #13. 종목이담긴
            screen_num = self.portfolio_stock_dict[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']      #14.KAO>실시간목록>주식체결 중 체결시간만 가져오기

                    #15. 라인 71 카피...실시간 조회에 맞게 수정
            self.dynamicCall('SetRealReg(QString, QString, QString, QString)', screen_num, code, fids, '1')
            print('실시간 등록 코드 : %s, 스크린번호: %s, fid 번호: %s' % (code, screen_num,fids))


    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICTrl.1')

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

    def real_event_slots(self): #1 실시간 관련 이벤트 생성. (KAO>개발도구>조회와 실시간이벤트처리>OnReceiveRealData() --
                               # 실시간 관련 이벤트가 여러개 있으므로 구분해 주기 위하여 (별도)함수 만듬
        self.OnReceiveRealData.connect(self.realdata_slot)


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
                    ls = line.split( '\t')

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

        cnt = 0  # 17. 스크린번호 할당
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


    def realdata_slot(self, sCode, sRealType, sRealData):     #2. 슬롯 함수 self.OnReceiveRealData.connect(self.realdata_slot) 구역을 만들어 줌.
        '''
        OnReceiveRealData(
          BSTR sCode,        // 종목코드
          BSTR sRealType,    // 리얼타입
          BSTR sRealData    // 실시간 데이터 전문
          )
        :return:
        '''

       # print(sCode)

        if sRealType == '장시작시간':   #10. 슬롯으로 와서 조건문 작성
            fid = self.realType.REALTYPE[sRealType]['장운영구분분']   #11. fid 번호 가져옴
            value = self.dynamicCall('GetCommRealData(QString, int)', sCode, fid)  #12. 실시간 꺼내오기  : 장시작전이므로 종목코드 빈값,

            if value == '0':
                print('장 시작 전')

            elif value == '3':
                print('장 시작')

            elif value == '2':
                print('장 종료, 동시호가로 넘어감')

            elif value == '4':
                print('3시30분 장 종료')

        elif sRealType == '주식체결' :         #16
            # print(sCode)

            a = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['체결시간'])  #16 체결시간 변수에 담음-- 스트링 형태로 나옴 HHMMSS
            b = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['현재가'])  #17  +, - 붙은 형태- 스트링
            b = abs(int(b))        #18 절대값 정수형 변환

            c = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['전일대비'])
            c = abs(int(c))

            d = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['등락율'])   # 18. 등략율은 + - 나오는 대로
            d = float(d)

            e = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['(최우선)매도호가'])
            e = abs(int(e))

            f = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['(최우선)매수호가'])
            f = abs(int(f))

            g = self.dynamicCall('GetCommRealData(QString, int)', sCode, self.realType.REALTYPE[sRealType]['거래량'])      #19. 1틱의 거래량
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
                self.portfolio_stock_dict.update({sCode:{}})         #20 종목코드 없는 경우 대비

            self.portfolio_stock_dict[sCode].update({'체결시간': a})     #21 실시간 데이터 업데이트
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




