from enformer_pytorch import seq_indices_to_one_hot
import torch
import pandas as pd
import numpy as np

def fasta_to_tensor(fasta_file):
    nucleotide_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
    with open(fasta_file, 'r') as f:
        lines = f.readlines()
        sequence = "".join(line.strip() for line in lines[1:])  # Ignore header
    seq_indices = [nucleotide_map.get(nt, 4) for nt in sequence]
    return torch.tensor(seq_indices).unsqueeze(0)  # Add batch dimension

seq = fasta_to_tensor("./data_/genotype_sequences.fasta")

# Required length based on Enformer model (adjust as per your model's config) 
required_length = 196608 
current_length = seq.shape[1] # Calculate padding needed 
if current_length < required_length: 
    padding_needed = required_length - current_length 
    seq = torch.nn.functional.pad(seq, (0, padding_needed), value=4) 
print("Padded sequence shape:", seq.shape) # Expected: (1, 196608)


# Load the extracted chr22 expression data 
bed_file = './data_/chr22_expression.bed' 
df = pd.read_csv(bed_file, sep='\t') # Inspect the dataframe 
# print(df.head())


# Extract expression values only (excluding genomic positions)
expression_values = df.iloc[:, 4:].values  # Only expression data columns

# Convert to numeric and handle missing values
expression_values = np.nan_to_num(expression_values, nan=0.0)

# Convert to PyTorch tensor
target_tensor = torch.tensor(expression_values, dtype=torch.float32)

# Ensure the target is in correct shape (batch_size, target_length, num_tracks)
target_tensor = target_tensor.unsqueeze(0)  # Adding batch dimension

#print("Target tensor shape:", target_tensor.shape)  # Should be (1, num_samples, num_tracks)
# finetune enformer on a limited budget

# print(torch.randint(0, 5, (1, 196_608 // 2,)).shape)
# print(torch.randn(1, 200, 128).shape)


# do your fine-tuning

import torch
from enformer_pytorch import from_pretrained
from enformer_pytorch.finetune import HeadAdapterWrapper

enformer = from_pretrained('EleutherAI/enformer-official-rough', use_tf_gamma = False)

model = HeadAdapterWrapper(
    enformer = enformer,
    num_tracks = 670,
    post_transformer_embed = False   # by default, embeddings are taken from after the final pointwise block w/ conv -> gelu - but if you'd like the embeddings right after the transformer block with a learned layernorm, set this to True
)#.cuda()

#seq = torch.randint(0, 5, (1, 196_608 // 2,))#.cuda()
#target = torch.randn(1, 200, 128)#.cuda()  # 128 tracks

# print(seq.shape)
# print(torch.unique(seq))

loss = model(seq, target = target_tensor)
loss.backward()
