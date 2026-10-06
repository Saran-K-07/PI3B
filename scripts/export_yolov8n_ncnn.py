"""Export YOLOv8n to ncnn for faster Pi 3B CPU inference.

Usage: python3 scripts/export_yolov8n_ncnn.py --imgsz 320
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="yolov8n.pt")
ap.add_argument("--imgsz", type=int, default=320, choices=[320, 416, 640])
args = ap.parse_args()

from ultralytics import YOLO

m = YOLO(args.model)
out = m.export(format="ncnn", imgsz=args.imgsz)
print(f"exported: {out}")
