# Aspect Lexicon

Seed keywords used to tag reviews with the service aspects they mention (first pass of the
two-pass aspect procedure; the second pass is an independent BERTopic run whose unmatched
topics are reviewed and added here). Matching is a case-insensitive substring match on the
normalised text and on the raw text, so English seeds survive Arabic normalisation and vice
versa. The authoritative copy of this table is `ASPECTS` in `src/aspects.py`.

| Aspect | English seeds | Arabic seeds |
|---|---|---|
| Login / authentication | login, log in, sign in, otp, password, uae pass, authentication | تسجيل الدخول, كلمة المرور, رمز |
| Payment | payment, pay, fee, card, refund, charge, invoice | دفع, رسوم, بطاقة, استرداد, فاتورة |
| Usability | easy, confusing, interface, ui, ux, navigate, design, simple | سهل, واجهة, معقد, تصميم |
| Performance / stability | slow, crash, freeze, lag, loading, bug, error | بطيء, يتوقف, تعليق, خطأ, بطء |
| Updates | update, version, upgrade, new version | تحديث, الاصدار, النسخة |
| Customer support | support, customer service, help, contact, response | دعم, خدمة العملاء, مساعدة, تواصل |
| Verification | verify, verification, emirates id, document, upload | تحقق, الهوية, مستند, رفع |
| Notifications | notification, alert, reminder, sms | اشعار, إشعار, تنبيه, رسالة |
| Language | arabic, english, translation, language | عربي, العربية, انجليزي, ترجمة, لغة |
| Registration | register, registration, sign up, account creation | تسجيل, حساب جديد, انشاء حساب |

Notes

- Arabic seeds are also matched in their normalised form (alef / ya / ta marbuta unified,
  diacritics removed) so that spelling variants are caught.
- Aspect tagging is applied to substantive reviews (six or more words); shorter reviews carry
  almost no aspect content.
- "Usability" and "Customer support" behave as markers of praise in this corpus (risk ratio
  below one), largely because of the seeds *easy* and *help*. They are kept in the lexicon so
  that the ranking is reported on the full pre-registered set.
