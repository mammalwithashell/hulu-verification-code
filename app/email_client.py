import dotenv
import imaplib
import os
from servers import servers
import email
from html2text import HTML2Text

h = HTML2Text()
h.ignore_links = True
dotenv.load_dotenv()

email_user = os.environ.get("USER")
pswrd = os.environ.get("PASS")
server = os.environ.get("SERVER")
mailbox = os.environ.get("MAILBOX")

def get_verification_code():
    try:
        imap_ssl = imaplib.IMAP4_SSL(host=servers[server], port=imaplib.IMAP4_SSL_PORT)
    except Exception as e:
        print(f"ErrorType : {type(e).__name__}, Error : {e}")
        return _, e

    try:
        imap_ssl.login(email_user, pswrd)
    except Exception as e:
        print(f"ErrorType : {type(e).__name__}, Error : {e.decode()}")
        return _, e


    imap_ssl.select(mailbox=mailbox, readonly=True)
    _, mail_ids = imap_ssl.search(None, "ALL")

    for mail_id in mail_ids[0].decode().split()[-2:]:
        return _get_code(imap_ssl, mail_id)

def _get_code(imap_ssl, mail_id):
    _, mail_data = imap_ssl.fetch(mail_id, '(RFC822)')
    message = email.message_from_bytes(mail_data[0][1])
    load =  message.get_payload()[0]
    payload = h.handle(load.get_payload())
    try:
        resp_code, response = imap_ssl.logout()
    except Exception as e:
        print(f"ErrorType : {type(e).__name__}, Error : {e.decode()}")
        return _, e

    return payload.split(".")[2].split()[0], ""

