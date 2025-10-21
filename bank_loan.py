import datetime


class BankLoan:
    def __init__(self, storage, personal):
        self.storage = storage
        self.personal = personal
        self.Max_loan = 10_000_000

    # db 최신화
    def _sync(self):
        self.personal.db = self.storage.load()
        return self.personal.db

    # 로그인 여부 검증
    def _require_login(self):
        if not self.personal.current_login:
            print("로그인 후 이용 가능합니다.")
            return False
        return True

    # 대출 신청
    def loan_request(self):
        if not self._require_login():
            return False

        db = self._sync()
        user = self.personal.find_user(self.personal.current_user_id)
        if not user:
            print("사용자 정보를 찾을 수 없습니다.")
            return False

        if not user.get("accounts"):
            print("대출 신청을 위해서는 계좌가 필요합니다.")
            return False

        # 대출 여부 확인
        if "loan" in user and user["loan"]["amount"] > 0:
            print(f"이미 대출이 존재합니다. (잔액: {user['loan']['amount']:,}원)")
            return False

        # 계좌 목록 출력
        print(f"\n[{user['name']}]님의 계좌 목록")
        for i, account in enumerate(user["accounts"], 1):
            for account_num, balance in account.items():
                print(f"{i}. 계좌번호: {account_num} | 잔액: {balance:,}원")

        account_number = input("대출금을 입금할 계좌번호를 입력하세요: ").strip()

        try:
            amount = int(input(f"대출 신청 금액을 입력하세요 (최대 {self.Max_loan:,}원): ").strip())
        except ValueError:
            print("잘못된 금액 입력입니다.")
            return False

        if amount <= 0 or amount > self.Max_loan:
            print("대출 신청 금액이 한도를 초과했거나 잘못되었습니다.")
            return False

        # 계좌 찾기 및 대출 실행
        for account in user["accounts"]:
            if account_number in account:
                account[account_number] += amount  # 대출금 입금
                user["loan"] = {
                    "amount": amount,
                    "date": str(datetime.datetime.now()),
                }
                try:
                    self.storage.save(db)
                except Exception as e:
                    print("저장 중 오류가 발생했습니다:", e)
                    return False
                print(f"{amount:,}원이 대출되었습니다. 계좌 {account_number}에 입금 완료.")
                return True

        print("해당 계좌번호를 찾을 수 없습니다.")
        return False

    # 대출 상환
    def loan_repayment(self):
        if not self._require_login():
            return False

        db = self._sync()
        user = self.personal.find_user(self.personal.current_user_id)
        if not user:
            print("사용자 정보를 찾을 수 없습니다.")
            return False

        # 대출 여부 확인
        if "loan" not in user or user["loan"]["amount"] <= 0:
            print("상환할 대출이 없습니다.")
            return False

        loan_amount = user["loan"]["amount"]
        print(f"\n현재 대출 잔액: {loan_amount:,}원")

        if not user.get("accounts"):
            print("상환을 위해서는 계좌가 필요합니다.")
            return False

        # 계좌 목록 출력
        print(f"\n[{user['name']}]님의 계좌 목록")
        for i, account in enumerate(user["accounts"], 1):
            for account_num, balance in account.items():
                print(f"{i}. 계좌번호: {account_num} | 잔액: {balance:,}원")

        account_number = input("상환할 계좌번호를 입력하세요: ").strip()

        try:
            amount = int(input(f"상환 금액을 입력하세요 (최대 {loan_amount:,}원): ").strip())
        except ValueError:
            print("잘못된 금액 입력입니다.")
            return False

        if amount <= 0:
            print("상환 금액은 0원보다 커야 합니다.")
            return False

        if amount > loan_amount:
            print("상환 금액이 대출 잔액을 초과할 수 없습니다.")
            return False

        # 계좌 찾기 및 상환 실행
        for account in user["accounts"]:
            if account_number in account:
                if account[account_number] < amount:
                    print("계좌 잔액이 부족합니다.")
                    return False

                # 상환 실행
                account[account_number] -= amount  # 계좌에서 출금
                user["loan"]["amount"] -= amount  # 대출 잔액 감소

                # 대출이 완전히 상환되면 대출 정보 삭제
                if user["loan"]["amount"] == 0:
                    del user["loan"]
                    print(f"{amount:,}원 상환 완료. 대출이 완전히 상환되었습니다!")
                else:
                    print(f"{amount:,}원 상환 완료. 남은 대출 잔액: {user['loan']['amount']:,}원")

                try:
                    self.storage.save(db)
                except Exception as e:
                    print("저장 중 오류가 발생했습니다:", e)
                    return False
                return True

        print("해당 계좌번호를 찾을 수 없습니다.")
        return False

    # 대출 조회
    def loan_inquiry(self):
        if not self._require_login():
            return False

        db = self._sync()
        user = self.personal.find_user(self.personal.current_user_id)
        if not user:
            print("사용자 정보를 찾을 수 없습니다.")
            return False

        if "loan" not in user or user["loan"]["amount"] <= 0:
            print("현재 대출이 없습니다.")
            return False

        loan_info = user["loan"]
        loan_date = datetime.datetime.fromisoformat(loan_info["date"].replace("Z", "+00:00"))

        print(f"\n=== 대출 정보 ===")
        print(f"대출 잔액: {loan_info['amount']:,}원")
        print(f"대출 일자: {loan_date.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
