"""
Fatigue Detection V2 Model
3-Class Classification: Alert, Non-Vigilant, Tired
Uses the best_fatigue_model2.pth model
"""

import os
import base64
import torch
import torch.nn as nn
from PIL import Image
from io import BytesIO
from torchvision import transforms

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_fatigue_model2.pth")

# Class labels for 3-class model
CLASS_LABELS = ['alert', 'non_vigilant', 'tired']

# --- Model Loading ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize model as None - will be loaded on startup
model = None


class FatigueCNN(nn.Module):
    """
    Custom CNN architecture for 3-class fatigue detection.
    Architecture matches the saved model weights:
    - Features: 4 blocks of Conv2d + BatchNorm + ReLU with MaxPooling
    - Classifier: 3 fully connected layers with BatchNorm and Dropout
    """
    def __init__(self, num_classes=3):
        super(FatigueCNN, self).__init__()
        
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25),
            
            # Block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25),
            
            # Block 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.25),
            
            # Block 4
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        
        # Classifier: 256 * 14 * 14 = 50176 (for 112x112 input)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(50176, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )
        
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


# Image transform - 112x112 input size for this model
transform = transforms.Compose([
    transforms.Resize((112, 112)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def load_fatigue_v2_model():
    """Load the 3-class fatigue detection model"""
    global model
    
    if not os.path.exists(MODEL_PATH):
        print(f"[WARNING] Fatigue V2 model not found: {MODEL_PATH}")
        return False
    
    try:
        print("[INFO] Loading FatigueCNN model...")
        
        # Load state dict
        checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=False)
        
        # Extract model state dict
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        
        # Create model and load weights
        model = FatigueCNN(num_classes=3)
        model.load_state_dict(state_dict, strict=True)
        model.to(device)
        model.eval()
        
        print(f"[SUCCESS] Fatigue V2 model loaded from {MODEL_PATH}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to load Fatigue V2 model: {e}")
        import traceback
        traceback.print_exc()
        return False


def decode_base64_image(base64_string):
    """Decode base64 image string to PIL Image"""
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data)).convert('RGB')
    return image


def predict_fatigue(image_base64):
    """
    Run fatigue prediction on a base64 encoded image
    Returns dict with predicted class and probabilities
    """
    if model is None:
        return {'error': 'Model not loaded'}
    
    try:
        # Decode image
        image = decode_base64_image(image_base64)
        
        # Preprocess for model
        input_tensor = transform(image).unsqueeze(0).to(device)
        
        # Run inference
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            
            # Get class probabilities
            prob_alert = probabilities[0].item() * 100
            prob_non_vigilant = probabilities[1].item() * 100
            prob_tired = probabilities[2].item() * 100
            
            # Get predicted class
            predicted_idx = torch.argmax(probabilities).item()
            predicted_class = CLASS_LABELS[predicted_idx]
            confidence = probabilities[predicted_idx].item() * 100
        
        return {
            'success': True,
            'predicted_class': predicted_class,
            'confidence': round(confidence, 1),
            'probabilities': {
                'alert': round(prob_alert, 1),
                'non_vigilant': round(prob_non_vigilant, 1),
                'tired': round(prob_tired, 1)
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def get_health_status():
    """Return health status for the fatigue v2 model"""
    model_loaded = model is not None
    return {
        'status': 'healthy' if model_loaded else 'degraded',
        'model_loaded': model_loaded,
        'device': str(device),
        'accuracy': 94.5,
        'classes': CLASS_LABELS
    }
