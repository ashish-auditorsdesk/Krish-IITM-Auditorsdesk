# install the necessary libraries like pip install doctr

import os
os.environ['USE_TORCH'] = '1'
import torch
from doctr.io import DocumentFile
from doctr.models import kie_predictor,ocr_predictor, db_resnet50, crnn_vgg16_bn


# taking our trained model as recognisation model and resnet as detection 
model = ocr_predictor(pretrained=True)

reco_model = crnn_vgg16_bn(pretrained=False, pretrained_backbone=False)
reco_model.load_state_dict(torch.load("crnn_vgg16_bn_20240326-104032.pt", map_location='cpu')) # Load the model weights from the .pt file
predictor = ocr_predictor(det_arch="db_resnet50", reco_arch=reco_model, pretrained=True)


doc = DocumentFile.from_pdf("Enter path to file")
result = predictor(doc)
# print(result)
words_values = []
for page in result.pages:
    for block in page.blocks:
        for line in block.lines:
            for word in line.words:
                words_values.append(word.value)

# printing the results 