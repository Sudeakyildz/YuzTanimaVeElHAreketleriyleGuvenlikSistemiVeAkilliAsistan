import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import pickle

# 1. Veri setini oku
csv_path = 'voice_commands.csv'
df = pd.read_csv(csv_path)

# NaN (boş) satırları temizle
df.dropna(inplace=True)

# 2. Eğitim ve test setine ayır
X_train, X_test, y_train, y_test = train_test_split(df['sentence'], df['label'], test_size=0.2, random_state=42)

# 3. Metinleri vektörleştir (TF-IDF)
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 4. Modeli eğit
model = LogisticRegression(max_iter=2000, class_weight='balanced', solver='liblinear', C=1.0)
model.fit(X_train_vec, y_train)

# 5. Test et
y_pred = model.predict(X_test_vec)
print('Doğruluk:', accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Test sonuçlarını kaydet
test_results = pd.DataFrame({'y_true': y_test, 'y_pred': y_pred})
test_results.to_csv('voice_command_test_results.csv', index=False)

# 6. Modeli kaydet
with open('voice_command_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('voice_vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

print('Model ve vektörizer kaydedildi.') 