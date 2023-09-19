import shortestPath

if __name__ == "__main__":
    with open("input.txt", "r", encoding="utf-8") as f:
        places_count, date, time = [int(i) for i in f.readline().split()]
        places = []
        for _ in range(places_count):
            lat, lon = [int(i) for i in f.readline().split()]
            places.append([lat, lon])
    
    
        
        