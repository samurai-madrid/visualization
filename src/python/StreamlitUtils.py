import streamlit as st

class ScaledProgressBar:
	def __init__(self, min, max):
		self.min = min
		self.scale = 1.0/(max - min)
		self.bar = st.progress(0)

	def progress(self, pr):
		self.bar.progress((pr - self.min) * self.scale)	