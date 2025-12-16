from ultralytics import YOLO
import cv2

# حمّلي الموديل الجديد
model = YOLO("runs/detect/train60/weights/best.pt")

# افتحي الكاميرا
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ الكاميرا مش بتفتح")
    exit()

print("✅ الكاميرا شغالة — اضغطي Q للخروج")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # inference
    results = model(frame, conf=0.5)

    # رسم البوكسات
    annotated_frame = results[0].plot()

    cv2.imshow("Helmet Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
