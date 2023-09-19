import requests
import zipfile


def downloadFile(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:

        with open(save_path, 'wb') as file:
            file.write(response.content)
        print("Pid data downloaded.")
        return 0
    else:
        print("Failed to download the file.")
        return 1

def extractFromFile(save_path):
    extract_to_directory = "pid_data"
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extract("stops.txt", extract_to_directory)
        zip_ref.extract("stop_times.txt", extract_to_directory)
        zip_ref.extract("trips.txt", extract_to_directory)
        zip_ref.extract("calendar.txt", extract_to_directory)
        zip_ref.extract("calendar_dates.txt", extract_to_directory)
    print(f"Pid files extracted.")

if __name__ == "__main__":
    url = "https://data.pid.cz/PID_GTFS.zip"
    save_path = "PID_GTFS.zip"

    downloadFile(url, save_path)
    extractFromFile(save_path)


