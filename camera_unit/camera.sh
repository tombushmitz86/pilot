# this bash script takes picture at local time as file name and sends it to the server
# once the image is takemn (syncronously)

DATE=$(date +"%Y-%m-%d_%H%M")

raspistill -vf -hf -o /home/pi/camera/$DATE.jpg

python send_picture.py $DATE
