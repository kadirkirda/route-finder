import pandas as pd
import numpy as np
import random
from haversine import haversine
import folium


class Route:
    sequence = []
    total_distance = -1
    distance_matrix = None

    def __init__(self, distance_matrix, route_size=None, sequence=None):
        self.distance_matrix = distance_matrix

        if route_size:
            self.create_random_sequence(route_size)
        elif sequence:
            self.sequence = sequence
        else:
            exit

        self.apply_2opt(distance_matrix)

        self.total_distance = self.get_distance(distance_matrix)

    def get_distance(self, distance_matrix):
        total_distance = 0
        sequence = self.sequence
        for i in range(0, len(sequence) - 1):
            total_distance += distance_matrix[sequence[i] - 1][sequence[i + 1] - 1]
        total_distance += self.distance_matrix[0][sequence[-1] - 1]
        return total_distance

    def apply_2opt(self, distance_matrix):
        n = len(self.sequence)
        new_sequence = self.sequence.copy()

        for i in range(0, n - 2):
            for j in range(i + 3, n):
                current_connection = (
                    distance_matrix[self.sequence[i] - 1][self.sequence[i + 1] - 1]
                    + distance_matrix[self.sequence[j - 1] - 1][self.sequence[j] - 1]
                )

                reversed_connection = (
                    distance_matrix[self.sequence[i] - 1][self.sequence[j - 1] - 1]
                    + distance_matrix[self.sequence[i + 1] - 1][self.sequence[j] - 1]
                )

                if reversed_connection < current_connection:
                    new_sequence[i + 1 : j] = self.sequence[j - 1 : i : -1].copy()
                    self.sequence = new_sequence.copy()
                    self.total_distance = self.get_distance(distance_matrix)

    def crossover(route1, route2, distance_matrix):
        sequence1 = route1.sequence
        sequence2 = route2.sequence
        sequence_length = len(sequence1)

        selected_number = random.randint(1, sequence_length)  # Starting point

        sequence1_index = sequence1.index(selected_number)
        sequence2_index = sequence2.index(selected_number)

        # Continue adding numbers until False
        sequence1_flag = True
        sequence2_flag = True

        # Empty route
        new_sequence = [0] * sequence_length

        new_sequence[0] = selected_number

        cursor_forward = 1
        cursor_backward = sequence_length - 1

        while sequence1_flag == True or sequence2_flag == True:
            if sequence1_flag == True:
                # Take the index to the beginning point if it is at the finish
                if sequence1_index == sequence_length - 1:
                    sequence1_index = 0
                else:
                    sequence1_index += 1

                # Is next value added? Then change flag to False
                # Else add next value to list
                if sequence1[sequence1_index] in new_sequence:
                    sequence1_flag = False
                else:
                    new_sequence[cursor_forward] = sequence1[sequence1_index]
                    cursor_forward += 1
            if sequence2_flag == True:
                # Take the index to the finish point if it is at the beginning
                if sequence2_index == 0:
                    sequence2_index = sequence_length - 1
                else:
                    sequence2_index -= 1

                # Is the next value added before? If yes, change the flag to False
                # Else add the next value to the list
                if sequence2[sequence2_index] in new_sequence:
                    sequence2_flag = False
                else:
                    new_sequence[cursor_backward] = sequence2[sequence2_index]
                    cursor_backward -= 1

        remaining_numbers = [x for x in sequence1 if x not in new_sequence]
        random.shuffle(remaining_numbers)

        for i in range(len(remaining_numbers)):
            new_sequence[cursor_forward] = remaining_numbers[i]
            cursor_forward += 1

        return Route(distance_matrix=distance_matrix, sequence=new_sequence)

    def mutation(sequence):
        size = len(sequence)
        selected_number = random.randint(1, size)
        random_index = random.randint(0, size - 1)
        new_sequence = list(sequence)
        new_sequence.remove(selected_number)
        new_sequence.insert(random_index, selected_number)
        return new_sequence

    def create_random_sequence(self, route_size):
        self.sequence = list(range(1, route_size + 1))
        random.shuffle(self.sequence)


class Population:
    __instance = None
    route_list = []  # Route List
    current_generation = -1
    route_size = None
    distance_matrix = None
    best_route = None
    best_distance = None
    mutation_percent = 0.01

    pop_size = -1
    number_of_children = -1

    def __init__(
        self,
        pop_size,
        route_size,
        number_of_children,
        distance_matrix,
        mutation_percent,
    ):
        self.pop_size = pop_size
        self.route_size = route_size
        self.number_of_children = number_of_children
        self.distance_matrix = distance_matrix
        self.mutation_percent = mutation_percent

        if Population.__instance != None:
            raise NotImplemented("This is a singleton class.")

        # Generate random population in given number
        for _ in list(range(pop_size)):
            self.route_list.append(
                Route(distance_matrix=distance_matrix, route_size=route_size)
            )

        self.sort()
        self.best_route = self.route_list[0]
        self.best_distance = self.best_route.total_distance
        self.current_generation = 0

    def parent_selection(self):
        parent_count = self.number_of_children * 2
        parent_list = []

        max_random = (self.pop_size * (self.pop_size + 1)) / 2

        for i in range(0, parent_count):
            k = 1
            random_value = random.randint(1, max_random)
            for j in range(0, self.pop_size):
                if random_value <= k:
                    parent_list.append(self.pop_size - j - 1)  # Reverse
                    break

                k = k + j + 2  # The next cumulative limit
        return parent_list

    def iterate_generation(self):
        """Creates the next generation by parameters."""
        parent_list = self.parent_selection()

        for i in range(0, self.number_of_children * 2, 2):
            route1 = self.route_list[parent_list[i]]
            route2 = self.route_list[parent_list[i + 1]]

            new_route = Route.crossover(route1, route2, self.distance_matrix)

            # If population has the route, don't add to the solution.
            if new_route in self.route_list:
                pass
            else:
                self.route_list.append(new_route)

        # Mutation operation
        random_value = random.random()
        if random_value < self.mutation_percent:
            selected_route = self.route_list[random.randint(0, self.pop_size - 1)]
            new_sequence = Route.mutation(selected_route.sequence)
            new_route = Route(
                distance_matrix=self.distance_matrix, sequence=new_sequence
            )
            self.route_list.append(new_route)

        # After adding new routes, sort all and remove surplus.
        self.sort()
        self.route_list = self.route_list[0 : self.pop_size]

        new_best_distance = self.route_list[0].total_distance

        improved_flag = False  # Flag for showing improvement

        if new_best_distance < self.best_distance:
            improved_flag = True
            self.best_distance = new_best_distance
            self.best_route = new_route

        self.current_generation += 1
        return improved_flag

    def sort(self):
        """Sorts route list in population by total distance."""
        self.route_list = sorted(
            self.route_list, key=lambda route: route.total_distance
        )


class GA_TSP:
    data = None
    population = None
    pop_size = -1
    route_size = -1
    number_of_children = -1
    max_generation = 0
    current_generation = -1
    mutation_percent = 0.05
    parent_list = []

    def __init__(self, data_path):
        self.data = Data(data_path)
        self.route_size = len(self.data.dataset)

    def set_problem(
        self, pop_size, number_of_children, max_generation, mutation_percent
    ):
        self.pop_size = pop_size
        self.number_of_children = number_of_children
        self.max_generation = max_generation
        self.mutation_percent = mutation_percent
        self.route_size = len(self.data.dataset)

        self.current_generation = 0

        self.population = Population(
            self.pop_size,
            self.route_size,
            self.number_of_children,
            self.data.distance_matrix,
            self.mutation_percent,
        )

    def draw_locations(self):
        lat_mean = np.mean(self.data.dataset["Latitude"])
        lon_mean = np.mean(self.data.dataset["Longitude"])

        coordinate = (lat_mean, lon_mean)
        m = folium.Map(tiles="Stamen Terrain", location=coordinate)

        sw = self.data.dataset[["Latitude", "Longitude"]].min().values.tolist()
        ne = self.data.dataset[["Latitude", "Longitude"]].max().values.tolist()

        m.fit_bounds([sw, ne])

        # Draw locations
        for i in range(len(self.data.dataset)):
            lat = self.data.dataset.at[i, "Latitude"]
            lon = self.data.dataset.at[i, "Longitude"]
            name = self.data.dataset.at[i, "Name"]
            folium.CircleMarker(
                [lat, lon],
                radius=2,
                popup=f"<div width=50px><b>{name}</b><br />lat:{lat}<br />lon:{lon}<div />",
                fill=True,
                color="purple",
            ).add_to(m)

        return m

    def draw_route(self, route):
        sequence = route.sequence

        lat_mean = np.mean(self.data.dataset["Latitude"])
        lon_mean = np.mean(self.data.dataset["Longitude"])

        coordinate = (lat_mean, lon_mean)
        m = folium.Map(tiles="Stamen Terrain", location=coordinate)

        sw = self.data.dataset[["Latitude", "Longitude"]].min().values.tolist()
        ne = self.data.dataset[["Latitude", "Longitude"]].max().values.tolist()

        m.fit_bounds([sw, ne])

        polyline_location_list = []

        for i in sequence:
            polyline_location_list.append(
                [
                    self.data.dataset.at[i - 1, "Latitude"],
                    self.data.dataset.at[i - 1, "Longitude"],
                ]
            )

        polyline_location_list.append(
            [
                self.data.dataset.at[sequence[0] - 1, "Latitude"],
                self.data.dataset.at[sequence[0] - 1, "Longitude"],
            ]
        )

        folium.PolyLine(locations=polyline_location_list, line_opacity=0.5).add_to(m)

        # Draw locations
        for i in range(len(self.data.dataset)):
            lat = self.data.dataset.at[i, "Latitude"]
            lon = self.data.dataset.at[i, "Longitude"]
            name = self.data.dataset.at[i, "Name"]
            folium.CircleMarker(
                [lat, lon],
                radius=2,
                popup=f"<div width=50px><b>{name}</b><br />lat:{lat}<br />lon:{lon}<div />",
                fill=True,
                color="purple",
            ).add_to(m)

        return m


class Data:
    dataset = None
    distance_matrix = None  # Get distances
    location_names = []

    def __init__(self, data_path):
        self.__set_data(data_path)
        self.__set_distance_matrix()

    def __set_data(self, data_path):
        self.dataset = pd.read_excel(data_path)
        self.location_names = self.dataset.Name.to_list()

    def __set_distance_matrix(self):
        n = len(self.location_names)  # Number of locations
        self.distance_matrix = np.zeros((n, n))

        for i in range(0, n):
            for j in range(0, i):
                if i != j:
                    self.distance_matrix[i, j] = haversine(
                        (
                            self.dataset.loc[i, "Latitude"],
                            self.dataset.loc[i, "Longitude"],
                        ),
                        (
                            self.dataset.loc[j, "Latitude"],
                            self.dataset.loc[j, "Longitude"],
                        ),
                    )
                    self.distance_matrix[j][i] = self.distance_matrix[i][j]
