import plotly.io as pio
pio.renderers.default = "browser"

import plotly.graph_objects as go

fig = go.Figure(data=[go.Bar(x=["Teste"], y=[10])])
fig.show()
