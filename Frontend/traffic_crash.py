import pandas as pd
import folium
import matplotlib.pyplot as plt
import requests
from ipywidgets import Dropdown, Output, HBox
from IPython.display import display
class road_crash:
    def __init__(self):
        pass

    def get_roads_list(self, roads_df1):
        red = []
        yellow = []
        green = []
        blue = []
        for road in range(0, len(roads_df1)):
            if roads_df1.iloc[road]['ALLVEHS_MMW'] < 1900:
                blue.append(roads_df1.iloc[road]['coordinates'])
            elif roads_df1.iloc[road]['ALLVEHS_MMW'] >= 1900 and roads_df1.iloc[road]['ALLVEHS_MMW'] < 5300:
                green.append(roads_df1.iloc[road]['coordinates'])
            elif roads_df1.iloc[road]['ALLVEHS_MMW'] >= 5300 and roads_df1.iloc[road]['ALLVEHS_MMW'] < 11000:
                yellow.append(roads_df1.iloc[road]['coordinates'])
            else:
                red.append(roads_df1.iloc[road]['coordinates'])
        return red, yellow, green, blue

    def drop_list(self, list):
        merge_list = []
        for l1 in list:
            for l2 in l1:
                merge_list.append(l2)
        return merge_list

    def check_crash_num(self, crash_df1, red, yellow, green, blue):
        red_crash = 0
        yellow_crash = 0
        green_crash = 0
        blue_crash = 0
        # Divide crashes into traffic flow lists of different sizes
        for crash in range(0, len(crash_df1)):
            red_compare = []
            yellow_compare = []
            green_compare = []
            blue_compare = []
            lon = crash_df1.iloc[crash]['Location'][0]
            lat = crash_df1.iloc[crash]['Location'][1]
            for coor in red:
                red_compare.append(abs(lon - coor[0]) + abs(lat - coor[1]))
            for coor2 in yellow:
                yellow_compare.append(abs(lon - coor2[0]) + abs(lat - coor2[1]))
            for coor3 in green:
                green_compare.append(abs(lon - coor3[0]) + abs(lat - coor3[1]))
            for coor4 in blue:
                blue_compare.append(abs(lon - coor4[0]) + abs(lat - coor4[1]))
            red_compare.sort()
            yellow_compare.sort()
            green_compare.sort()
            blue_compare.sort()
            comp_dic = {"red": red_compare[0], "yellow": yellow_compare[0], "green": green_compare[0],
                        "blue": blue_compare[0]}
            min_group = min(comp_dic, key=comp_dic.get)
            if min_group == "red":
                red_crash += 1
            elif min_group == "yellow":
                yellow_crash += 1
            elif min_group == "green":
                green_crash += 1
            else:
                blue_crash += 1
        return red_crash, yellow_crash, green_crash, blue_crash

    def draw_map(self, roads_df1, map):
        num = -1
        for road in roads_df1['OBJECTID']:
            num += 1
            coords_list = roads_df1.loc[roads_df1['OBJECTID'] == road]['coordinates'][str(num)]
            swapped_coords_list = [[coord[1], coord[0]] for coord in coords_list]
            if roads_df1.loc[roads_df1['OBJECTID'] == road]['ALLVEHS_MMW'][str(num)] < 1900:
                ls = folium.PolyLine(locations=swapped_coords_list, color='blue')
            elif roads_df1.loc[roads_df1['OBJECTID'] == road]['ALLVEHS_MMW'][str(num)] >= 1900 and \
                    roads_df1.loc[roads_df1['OBJECTID'] == road]['ALLVEHS_MMW'][str(num)] < 5300:
                ls = folium.PolyLine(locations=swapped_coords_list, color='green')
            elif roads_df1.loc[roads_df1['OBJECTID'] == road]['ALLVEHS_MMW'][str(num)] >= 5300 and \
                    roads_df1.loc[roads_df1['OBJECTID'] == road]['ALLVEHS_MMW'][str(num)] < 11000:
                ls = folium.PolyLine(locations=swapped_coords_list, color='yellow')
            else:
                ls = folium.PolyLine(locations=swapped_coords_list, color='red')
            ls.add_to(map)
        legend_html = """
        <div style="position: fixed;
             bottom: 20px; left: 20px; width: 200px; height: 100px;
             border:2px solid grey; z-index:9999; font-size:12px;
             background-color: white;
             ">
             &nbsp; <strong>traffic flow</strong> <br>
             &nbsp; <font color="black">&#9648; Red Line: x>=11000</font><br>
             &nbsp; <font color="black">&#9648; Yellow Line: 5300<=x<11000</font><br>
             &nbsp; <font color="black">&#9648; Green Line: 1900<=x<5300</font><br>
             &nbsp; <font color="black">&#9648; Blue Line: x<=1900</font><br>
        </div>
        """
        map.get_root().html.add_child(folium.Element(legend_html))

    def add_point(self, crash_df1, map):
        crash_list = crash_df1['Location']
        swapped_crash_list = [[coord[1], coord[0]] for coord in crash_list]
        for crash in range(0, len(swapped_crash_list)):
            pop_content = "degree of injury:", str(crash_df1['INJ_OR_FATAL'][str(crash)])
            folium.Marker(location=swapped_crash_list[crash], popup=pop_content).add_to(map)

    def plot_pie_chart(self, categories, values, title):
        plt.pie(values, labels=categories, autopct='%1.1f%%', colors=['blue', 'green', 'yellow', 'red'])
        plt.title(title)
        plt.axis('equal')
        plt.show()

    def show_crashtype(self,acc_list):
        choose_acc = Dropdown(
            options=acc_list,
            description='Accidents types:',
        )
        output_acc = Output()

        def choiceX(change):
            with output_acc:
                output_acc.clear_output()
                formatted_accident_type = change.new.replace(" ", "%20")
                url_endpoint = "http://127.0.0.1:9090/traffic/vol-vs-crash/"
                url = url_endpoint + formatted_accident_type
                response_tra_acc = requests.get(url)

                if response_tra_acc.status_code == 200:
                    data_tra_fic = response_tra_acc.json()
                    if "error" in data_tra_fic:
                        print("Error:", data_tra_fic["error"])
                    else:
                        volume = data_tra_fic.get('volume', [])
                        counts = data_tra_fic.get('counts', [])
                        thresold = [1900, 5300, 11000]
                        vc = {"blue":0, "green":0, "yellow":0, "red":0}
                        for idx in range(len(volume)):
                            vol = volume[idx]
                            if vol<thresold[0]:
                                vc["blue"] += counts[idx]
                            elif vol<thresold[1]:
                                vc["green"] += counts[idx]
                            elif vol<thresold[2]:
                                vc["yellow"] += counts[idx]
                            else:
                                vc["red"] += counts[idx]
                        cl = [vc["blue"], vc["green"], vc["yellow"], vc["red"]]
                        
                        plt.figure(figsize=(10, 5))
                        rects = plt.bar(range(len(cl)), cl, color=['b', 'g', 'y', 'r'], alpha=0.8,width=0.5)
                        plt.title('Traffic Volume VS. Number of Collision for ' + change.new, fontdict={"fontsize":16, "fontweight":'bold'})
                        plt.xlabel('Traffic Volume',fontdict={"fontsize":14})
                        plt.ylabel('Number of Collisions',fontdict={"fontsize":14})
                        plt.grid(True)
                        for rect in rects:
                            height = rect.get_height()
                            plt.text(rect.get_x()+rect.get_width()/2,height,str(height),ha='center',fontdict={"fontsize":12, "fontweight":'bold'})
                        xticks = ["0~1900(Low)", "1900~5300(Medium-Low)", "5300~11000(Medium-High)", "above 11000(High)"]
                        plt.xticks(range(len(cl)),xticks)
                        plt.show()
                else:
                    print("Error:", response_tra_acc.status_code)

        # Attach the event handler
        choose_acc.observe(choiceX, names='value')

        ui = HBox([choose_acc])
        display(ui, output_acc)

    def show_pol(self, pol_list):
        choose_pol = Dropdown(
            options=pol_list,
            description='Pollutant types:',
        )

        output_pol = Output()

        def choiceZ(change):
            with output_pol:
                output_pol.clear_output()
                url_endpoint = "http://127.0.0.1:9090/traffic/vol-vs-epa/"
                # Define the URL
                url_poll = url_endpoint + change.new
                # Send a GET request to the URL
                response_pol = requests.get(url_poll)

                if response_pol.status_code == 200:
                    # Parse the JSON response
                    data_poll = response_pol.json()
                    # Check if the response contains an error message
                    if "error" in data_poll:
                        # Handle the error case
                        error_message = data_poll["error"]
                        print("Error:", error_message)
                    else:
                        # Extract traffic_volumes_values and collision_counts_values from the JSON data
                        volume = data_poll.get('volume', [])
                        counts = data_poll.get('counts', [])
                        thresold = [1900, 5300, 11000]
                        vc = {"blue":0, "green":0, "yellow":0, "red":0}
                        for idx in range(len(volume)):
                            vol = volume[idx]
                            if vol<thresold[0]:
                                vc["blue"] += counts[idx]
                            elif vol<thresold[1]:
                                vc["green"] += counts[idx]
                            elif vol<thresold[2]:
                                vc["yellow"] += counts[idx]
                            else:
                                vc["red"] += counts[idx]
                        cl = [vc["blue"], vc["green"], vc["yellow"], vc["red"]]

                        plt.show()
                        plt.figure(figsize=(10, 6))
                        rects = plt.bar(range(len(cl)), cl, color=['b', 'g', 'y', 'r'], alpha=0.8,width=0.5)
                        plt.title(f'Traffic Volume vs. Number of {change.new} Events', fontdict={"fontsize":16, "fontweight":'bold'})
                        plt.xlabel('Traffic Volume (vehicles per day)',fontdict={"fontsize":14})
                        plt.ylabel(f'Number of {change.new} Events',fontdict={"fontsize":14})
                        plt.grid(True)
                        for rect in rects:
                            height = rect.get_height()
                            plt.text(rect.get_x()+rect.get_width()/2,height,str(height),ha='center',fontdict={"fontsize":12, "fontweight":'bold'})
                        xticks = ["0~1900(Low)", "1900~5300(Medium-Low)", "5300~11000(Medium-High)", "above 11000(High)"]
                        plt.xticks(range(len(cl)),xticks)
                        plt.show()
                else:
                    print("Error:", response_pol.status_code)

        choose_pol.observe(choiceZ, names='value')

        ui = HBox([choose_pol])

        display(ui)
        display(output_pol)