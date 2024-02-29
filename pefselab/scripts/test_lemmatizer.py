import lemmatize
import sys

lemmatizer = lemmatize.SUCLemmatizer()
lemmatizer.load('suc-saldo.lemmas')

print('%.2f%%' % (100.0*lemmatizer.evaluate(sys.argv[1])))

