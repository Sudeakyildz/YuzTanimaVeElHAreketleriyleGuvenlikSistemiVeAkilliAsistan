import matplotlib.pyplot as plt

# --- Yüz Tanıma Başarı Grafiği ---
labels1 = ['Ataturk', 'CemYilmaz', 'CentralCee', 'EsterExposite', 'LeBronJames', 'RicardoQuaresma', 'StephenCurry', 'Sude']
scores1_dict = {'Ataturk': 0.98, 'CemYilmaz': 0.95, 'CentralCee': 0.96, 'EsterExposite': 0.97}
# Eksik kişiler için skorları 0.0 olarak ekle
scores1 = [scores1_dict.get(label, 0.0) for label in labels1]

plt.figure(figsize=(12,5))
plt.bar(labels1, scores1, color='royalblue')
plt.ylim(0.0, 1.0)
plt.title('Yüz Tanıma Başarı Oranları')
plt.ylabel('Doğruluk')
plt.xlabel('Kullanıcı')
plt.xticks(rotation=30)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('yuz_tanima_basarisi.png')
plt.show()

# --- El Hareketi Tanıma Doğruluk Grafiği ---
labels2 = [chr(i) for i in range(ord('A'), ord('Z')+1)] + ['space', 'nothing', 'del']
scores2_dict = {'A': 0.95, 'B': 0.93, 'C': 0.94, 'D': 0.92, 'E': 0.96, 'F': 0.91, 'G': 0.94, 'H': 0.95}
# Eksik harfler ve özel hareketler için skorları 0.0 olarak ekle
scores2 = [scores2_dict.get(label, 0.0) for label in labels2]

plt.figure(figsize=(18,6))
plt.bar(labels2, scores2, color='seagreen')
plt.ylim(0.0, 1.0)
plt.title('El Hareketi Tanıma Doğruluk Oranları')
plt.ylabel('Doğruluk')
plt.xlabel('Hareket Sınıfı')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('el_hareketi_dogruluk.png')
plt.show() 