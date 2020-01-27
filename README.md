# U.S. Energy consumption: Sustainability Analysis


The Oxford Dictionary defines sustainability as the "[a]voidance of the
depletion of natural resources in order to maintain an ecological balance." In
recent years, sustainability has become a hot topic regarding energy consumption,
as fossil fuel reserves are predicted to completely deplete within the next 110
years or so (BP Statistical Review of World Energy 2016). Yet, U.S. energy
consumption has more than doubled since 1960, steadily increasing all the while
with nonrenewable energy currently accounting for 88% of total consumption. One
way to to take action against this trajectory is to analyze the behavior of the most sustainable U.S. states and apply our learnings to states which are far
behing.

In order to do so, I define three metrics for sustainability that will
allow us to answer questions like:
- Which states are most sustainable?
- How do they consume energy by sector and fuel type?
- What can we learn and apply from these states?

The metrics I propose to quantify sustainability are:
1. **Effort Score:** a measure of how much a state's nonrenewable and renewable
energy consumption converge from 2000-2017.
2. **Green Score:** a measure of the average ratio of renewable energy
consumption to nonrenewable energy consumption from 2000-2017.
3. **Sustainability Index:** a weighted average of the Effort Score and Green
Score of a particular state. The user defines the weights of each of the two
component scores.

### The Tool: U.S. Energy Consumption Trends Dashboard

The outcome of this project is an interactive web app made using Dash by Plotly.
It allows the user to define how the sustainability index is calculated and then
immediately visualize it on a map of the United States. Once a state of interest
has been identified, the user can scroll down the page to view a breakdown of
any state's renewable and nonrenewable energy consumption by either sector or
fuel type.

### Future Directions

Currently, the Sustainability Index does not account for state population.
Factoring population into energy consumption to obtain energy consumption per
capita will likely produce different results. It will also allow for interesting
EDA such as average individual energy consumption by state.

I'm also interested in examining if correlation exists between state GDP and
energy consumption.

The dashboard currently only supports fuel consumption breakdown by "Total All
Sectors." I'd like to include the option to view a full breakdown of fuels by
any sector and to reorganize the layout for more intuitive use.
