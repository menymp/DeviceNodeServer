import time
import cv2
import numpy as np
import requests

poll_interval = 0.2  # seconds between polls

def fetch_image_bytes(url, timeout=5):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content

def decode_image(img_bytes):
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def main():
    url = "http://localhost:9090/latest/841FE8701120MenyEspCam1"
    while True:
        try:
            img_bytes = fetch_image_bytes(url, timeout=5)
            img = decode_image(img_bytes)
            if img is None:
                print(f"failed to decode image from {url}")
                time.sleep(poll_interval)
                continue

            # --- HERE ADD THE FRAME ---
            cv2.imshow("Camera Feed", img)

            # break if user presses 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except requests.RequestException as e:
            print(f"failed to fetch image; retrying: {e}")
            time.sleep(poll_interval)
        except Exception as e:
            print(f"unexpected error in main loop: {e}")
            time.sleep(poll_interval)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
