import torch.nn as nn
import torch.nn.functional as F
import torch
from torchvision.models import vgg19
import math
from numba import jit

class GELU(nn.Module):
	"""
	GELU activation approx. courtesy of 
	https://arxiv.org/pdf/1606.08415.pdf
	
	(note numba)
	"""
	@jit
	def forward(self, x):
		return 0.5 * x * (1 + torch.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * torch.pow(x, 3))))


class ResidualBlock(nn.Module):
	def __init__(self, in_features):
		super(ResidualBlock, self).__init__()
		self.conv_block = nn.Sequential(
			nn.Conv2d(in_features, in_features, kernel_size=3, stride=1, padding=1),
			GELU(),
			nn.Conv2d(in_features, in_features, kernel_size=3, stride=1, padding=1),
		)

	def forward(self, x):
		return self.conv_block(x)
		
		
class Generator(nn.Module):
	def __init__(self, in_channels=3, out_channels=3, residual_blocks=10):
		super(Generator, self).__init__()
		self.conv1 = nn.Sequential(
						nn.Conv2d(in_channels, 64, kernel_size=9, stride=1, padding=4), 
						GELU())

		# Residual blocks
		residuals = []
		for _ in range(residual_blocks):
			residuals.append(ResidualBlock(64))
		self.residuals = nn.Sequential(*residuals)
		
		#nearest neighbor upsample 
		self.upsample = nn.Sequential(
				nn.Upsample(scale_factor=2),
				nn.Conv2d(64, 64, 3, 1, 1),
				GELU(),
				nn.Upsample(scale_factor=2),
				nn.Conv2d(64, 64, 3, 1, 1),
				GELU())
		self.conv3 = nn.Sequential(nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1), GELU())
		self.conv4 = nn.Sequential(nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=4))

	def forward(self, x):
		out = self.conv1(x)
		out = self.residuals(out1)
		out = self.conv2(out)
		i_bicubic= self.upsample(out)
		out = self.conv3(out)
		i_res = self.conv4(out) 
		out = torch.add(i_bicubic + i_res)
		return out
		
class Discriminator(nn.Module):
	def __init__(self, input_shape):
		super(Discriminator, self).__init__()
		layers = []
		self.input_shape = input_shape
		in_channels, in_height, in_width = self.input_shape
		self.output_shape = (1, 8, 8)

		def discriminator_block(in_filters, out_filters, first_block=False):
			layers = []
			layers.append(nn.Conv2d(in_filters, out_filters, kernel_size=3, stride=1, padding=1))
			layers.append(nn.Dropout(0.3))
			if not first_block:
				layers.append(nn.BatchNorm2d(out_filters))
			layers.append(nn.LeakyReLU(0.2, inplace=True))
			layers.append(nn.Conv2d(out_filters, out_filters, kernel_size=3, stride=2, padding=1))
			layers.append(nn.Dropout(0.3))
			layers.append(nn.BatchNorm2d(out_filters))
			layers.append(nn.LeakyReLU(0.2, inplace=True))
			return layers

		in_filters = in_channels
		for i, out_filters in enumerate([16, 32,64, 128, 256, 512]):
			layers.extend(discriminator_block(in_filters, out_filters, first_block=(i == 0)))
			in_filters = out_filters

		layers.append(nn.Conv2d(out_filters, 1, kernel_size=3, stride=1, padding=1))

		self.model = nn.Sequential(*layers)

	def forward(self, img):
		return self.model(img)
		
		
		
		
		