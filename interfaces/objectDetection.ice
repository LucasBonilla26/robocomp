//******************************************************************
// 
//  Generated by IDSL to IDL Translator
//  
//  File name: objectDetection.idl
//  Source: objectDetection.idsl
//  
//******************************************************************   
#ifndef ROBOCOMPOBJECTDETECTION_ICE
#define ROBOCOMPOBJECTDETECTION_ICE

module RoboCompobjectDetection{
	sequence <string> listType;

	interface objectDetection{
		void  aprilFitModel(string model);
		void  fitModel(string model, string method);
		void  getInliers(string model);
		void  projectInliers(string model);
		void  convexHull(string model);
		void  extractPolygon(string model);
		void  ransac(string model);
		void  normalSegmentation(string model);
		void  euclideanClustering(out int numClusters);
		void  showObject(int numObject);
		void  reset();
		void  vfh(int numObject);
		void  loadVFH();
	};
};
  
#endif