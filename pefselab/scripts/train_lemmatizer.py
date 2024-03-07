import lemmatize
import sys

lemmatizer = lemmatize.train([sys.argv[1]], [sys.argv[2]])
lemmatizer.save("suc-saldo.lemmas")
