# KOARCH
Development of a reference architecture for machine optimization based on computational intelligence and big data.

Conventional manufacturing plants reach their limits due to dynamic developments on the global markets, increasing product variety and complexity as well as continuously increasing requirements on system software. Computational intelligence methods promise flexible adaption and extension of the plants, while being able to automatically detect invalid system states, applying condition monitoring and predictive control and maintenance. Additionally, consumption of resources, i.e. time and energy, can be optimized. However, the integration of suitable solutions in companies often fails. 

The main goal of KOARCH is to minimize the manual effort to make computational intelligence methods available to the industry. Therefore, generic approaches from data acquisition and modelling up to the generation of operation instructions are combined in an architectural manner. The required technologies are already available, but not yet capable of the required collaboration.

The KOARCH researchers can draw on results and knowledge of several related projects. In this research project incorporated are the Institute for Data Science, Engineering, and Analytics (IDE+A) and the Institute for Computer Science from the faculty of Computer Science and Engineering from the TH Köln, the Institute Industrial IT (inIT) of the OWL University of Applied Sciences in Lemgo as well as partners from the industry.

The Github Repository is structured as follows:

- Big Data Platform\
  Contains the building blocks for [Docker](Big_Data_Platform/Docker/readme.md) and [Kubernetes](Big_Data_Platform/Kubernetes/readme.md)
- Use Cases
  - [Social Media Emotion Detection](Use_Cases/other/Social_Media_Emotion_Detection/readme.md)\
  The social media use case collects tweets from Twitter and analyses the text.
  This first iteration proves the architectural foundations and shows the containerization and communication of the independent modules.
  - [VPS Popcorn Production](Use_Cases/VPS_Popcorn_Production/Docker/readme.md)\
  The VPS use case optimizes the production of popcorn through the simultaneous execution and evaluation of several machine learning algorithms.
  This second iteration implements the cognition module and several APIs for information storage and retrieval.

The project "KOARCH" is sponsored by the German Federal Ministry of Education and Research (BMBF) under funding code 13FH007IA6 and 13FH007IB6.

<img src="./docs/BMBF.jpg" width="200px">
