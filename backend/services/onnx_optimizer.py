import torch
from transformers import AutoTokenizer, AutoModel
from optimum.onnxruntime import ORTModelForSequenceClassification, ORTOptimizer
from optimum.onnxruntime.configuration import OptimizationConfig
import onnxruntime as ort
from pathlib import Path
import logging
import time
from typing import Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class ONNXOptimizer:
    def __init__(self):
        self.model_cache_dir = Path("models/onnx")
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ONNX Optimizer initialized")
    
    def convert_to_onnx(
        self,
        model_name: str,
        task: str = "feature-extraction",
        quantize: bool = True
    ) -> str:
        try:
            logger.info(f"Converting {model_name} to ONNX...")
            output_path = self.model_cache_dir / model_name.replace("/", "_")
            output_path.mkdir(exist_ok=True)
            
            logger.info("Step 1/3: Exporting to ONNX format...")
            ort_model = ORTModelForSequenceClassification.from_pretrained(
                model_name,
                export=True,
                provider="CPUExecutionProvider"
            )
            
            logger.info("Step 2/3: Optimizing ONNX graph...")
            optimizer = ORTOptimizer.from_pretrained(ort_model)
            
            optimization_config = OptimizationConfig(
                optimization_level=99,
                optimize_for_gpu=torch.cuda.is_available(),
                enable_gelu_approximation=True,
                enable_gemm_fast_gelu=True,
                enable_layer_norm_fusing=True,
                enable_attention_fusing=True,
                enable_skip_layer_norm_fusing=True,
                enable_bias_skip_layer_norm_fusing=True,
            )
            
            optimizer.optimize(
                save_dir=output_path,
                optimization_config=optimization_config
            )
            
            if quantize:
                logger.info("Step 3/3: Quantizing model...")
                self._quantize_model(output_path)
            
            logger.info(f"✓ Model converted successfully to: {output_path}")
            self._benchmark_model(model_name, output_path)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"ONNX conversion error: {str(e)}")
            raise
    
    def _quantize_model(self, model_path: Path):
        from onnxruntime.quantization import quantize_dynamic, QuantType
        
        onnx_model_path = model_path / "model.onnx"
        quantized_model_path = model_path / "model_quantized.onnx"
        
        if not onnx_model_path.exists():
            logger.warning(f"Model not found: {onnx_model_path}")
            return
        
        quantize_dynamic(
            model_input=str(onnx_model_path),
            model_output=str(quantized_model_path),
            weight_type=QuantType.QInt8,
            optimize_model=True
        )
        
        original_size = onnx_model_path.stat().st_size / (1024 * 1024)
        quantized_size = quantized_model_path.stat().st_size / (1024 * 1024)
        reduction = ((original_size - quantized_size) / original_size) * 100
        
        logger.info(f"Quantization complete:")
        logger.info(f"  Original: {original_size:.2f} MB")
        logger.info(f"  Quantized: {quantized_size:.2f} MB")
        logger.info(f"  Reduction: {reduction:.1f}%")
    
    def _benchmark_model(self, model_name: str, onnx_path: Path):
        logger.info("Benchmarking model performance...")
        try:
            from transformers import AutoModel
            pytorch_model = AutoModel.from_pretrained(model_name)
            pytorch_model.eval()
            
            onnx_model_path = onnx_path / "model_quantized.onnx"
            if not onnx_model_path.exists():
                onnx_model_path = onnx_path / "model.onnx"
            
            ort_session = ort.InferenceSession(str(onnx_model_path))
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            text = "This is a test sentence for benchmarking."
            inputs = tokenizer(text, return_tensors="pt")
            
            pytorch_times = []
            for _ in range(100):
                start = time.time()
                with torch.no_grad():
                    _ = pytorch_model(**inputs)
                pytorch_times.append(time.time() - start)
            
            avg_pytorch_time = np.mean(pytorch_times) * 1000
            
            onnx_times = []
            onnx_inputs = {
                "input_ids": inputs["input_ids"].numpy(),
                "attention_mask": inputs["attention_mask"].numpy()
            }
            
            for _ in range(100):
                start = time.time()
                _ = ort_session.run(None, onnx_inputs)
                onnx_times.append(time.time() - start)
            
            avg_onnx_time = np.mean(onnx_times) * 1000
            speedup = ((avg_pytorch_time - avg_onnx_time) / avg_pytorch_time) * 100
            
            logger.info("=" * 60)
            logger.info("BENCHMARK RESULTS")
            logger.info("=" * 60)
            logger.info(f"PyTorch inference time: {avg_pytorch_time:.2f} ms")
            logger.info(f"ONNX inference time: {avg_onnx_time:.2f} ms")
            logger.info(f"Speedup: {speedup:.1f}% faster")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.warning(f"Benchmark failed: {str(e)}")
    
    def load_onnx_model(self, model_path: str) -> ort.InferenceSession:
        model_path = Path(model_path)
        onnx_file = model_path / "model_quantized.onnx"
        if not onnx_file.exists():
            onnx_file = model_path / "model.onnx"
        
        if not onnx_file.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4
        
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider']
        
        session = ort.InferenceSession(
            str(onnx_file),
            sess_options=sess_options,
            providers=providers
        )
        
        logger.info(f"Loaded ONNX model from: {onnx_file}")
        return session
