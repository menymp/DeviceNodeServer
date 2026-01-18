-- MySQL dump 10.13  Distrib 8.0.30, for Win64 (x86_64)
--
-- Host: localhost    Database: mechlabenviroment
-- ------------------------------------------------------
-- Server version	8.0.30

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `controlstypes`
--

DROP TABLE IF EXISTS `controlstypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `controlstypes` (
  `idControlsTypes` int NOT NULL AUTO_INCREMENT,
  `TypeName` varchar(45) DEFAULT NULL,
  `controlTemplate` json DEFAULT NULL,
  PRIMARY KEY (`idControlsTypes`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dashboardcontrolt`
--

DROP TABLE IF EXISTS `dashboardcontrolt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dashboardcontrolt` (
  `idControl` int NOT NULL AUTO_INCREMENT,
  `Name` varchar(45) DEFAULT NULL,
  `idType` int NOT NULL,
  `idUser` int NOT NULL,
  `parameters` json DEFAULT NULL,
  PRIMARY KEY (`idControl`),
  KEY `fk_dashboardControlT_ControlsTypes1_idx` (`idType`),
  KEY `fk_dashboardControlT_users1_idx` (`idUser`),
  CONSTRAINT `fk_dashboardControlT_ControlsTypes1` FOREIGN KEY (`idType`) REFERENCES `controlstypes` (`idControlsTypes`),
  CONSTRAINT `fk_dashboardControlT_users1` FOREIGN KEY (`idUser`) REFERENCES `users` (`idUser`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `devices`
--

DROP TABLE IF EXISTS `devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devices` (
  `idDevices` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) DEFAULT NULL,
  `idMode` int NOT NULL,
  `idType` int NOT NULL,
  `channelPath` varchar(45) DEFAULT NULL,
  `idParentNode` int NOT NULL,
  PRIMARY KEY (`idDevices`),
  KEY `fk_Devices_DevicesModes1_idx` (`idMode`),
  KEY `fk_Devices_DevicesType1_idx` (`idType`),
  KEY `fk_Devices_NodesTable1_idx` (`idParentNode`),
  CONSTRAINT `fk_Devices_DevicesModes1` FOREIGN KEY (`idMode`) REFERENCES `devicesmodes` (`idDevicesModes`),
  CONSTRAINT `fk_Devices_DevicesType1` FOREIGN KEY (`idType`) REFERENCES `devicestype` (`idDevicesType`),
  CONSTRAINT `fk_Devices_NodesTable1` FOREIGN KEY (`idParentNode`) REFERENCES `nodestable` (`idNodesTable`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `devicesmeasures`
--

DROP TABLE IF EXISTS `devicesmeasures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devicesmeasures` (
  `idDevicesMeasures` int NOT NULL AUTO_INCREMENT,
  `value` varchar(45) DEFAULT NULL,
  `uploadDate` timestamp NULL DEFAULT NULL,
  `idDevice` int NOT NULL,
  PRIMARY KEY (`idDevicesMeasures`),
  KEY `fk_DevicesMeasures_Devices1_idx` (`idDevice`),
  CONSTRAINT `fk_DevicesMeasures_Devices1` FOREIGN KEY (`idDevice`) REFERENCES `devices` (`idDevices`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `devicesmodes`
--

DROP TABLE IF EXISTS `devicesmodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devicesmodes` (
  `idDevicesModes` int NOT NULL AUTO_INCREMENT,
  `mode` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idDevicesModes`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `devicestype`
--

DROP TABLE IF EXISTS `devicestype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devicestype` (
  `idDevicesType` int NOT NULL AUTO_INCREMENT,
  `type` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idDevicesType`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nodestable`
--

DROP TABLE IF EXISTS `nodestable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nodestable` (
  `idNodesTable` int NOT NULL AUTO_INCREMENT,
  `nodeName` varchar(45) DEFAULT NULL,
  `nodePath` varchar(45) DEFAULT NULL,
  `idDeviceProtocol` int NOT NULL,
  `idOwnerUser` int NOT NULL,
  `connectionParameters` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`idNodesTable`),
  KEY `fk_NodesTable_supportedProtocols_idx` (`idDeviceProtocol`),
  KEY `fk_NodesTable_users1_idx` (`idOwnerUser`),
  CONSTRAINT `fk_NodesTable_supportedProtocols` FOREIGN KEY (`idDeviceProtocol`) REFERENCES `supportedprotocols` (`idsupportedProtocols`),
  CONSTRAINT `fk_NodesTable_users1` FOREIGN KEY (`idOwnerUser`) REFERENCES `users` (`idUser`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `supportedprotocols`
--

DROP TABLE IF EXISTS `supportedprotocols`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supportedprotocols` (
  `idsupportedProtocols` int NOT NULL AUTO_INCREMENT,
  `ProtocolName` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idsupportedProtocols`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `idUser` int NOT NULL AUTO_INCREMENT,
  `username` varchar(45) NOT NULL,
  `pwd` varchar(45) NOT NULL,
  `email` varchar(45) DEFAULT NULL,
  `registerdate` timestamp NULL DEFAULT NULL,
  `telegrambotToken` varchar(255) DEFAULT NULL,
  `userState` int DEFAULT NULL,
  PRIMARY KEY (`idUser`),
  UNIQUE KEY `username_UNIQUE` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `videodashboard`
--

DROP TABLE IF EXISTS `videodashboard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `videodashboard` (
  `idvideoDashboard` int NOT NULL AUTO_INCREMENT,
  `configJsonFetch` json DEFAULT NULL,
  `idOwnerUser` int NOT NULL,
  PRIMARY KEY (`idvideoDashboard`),
  KEY `fk_videoDashboard_users1_idx` (`idOwnerUser`),
  CONSTRAINT `fk_videoDashboard_users1` FOREIGN KEY (`idOwnerUser`) REFERENCES `users` (`idUser`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `videosources`
--

DROP TABLE IF EXISTS `videosources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `videosources` (
  `idVideoSource` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) DEFAULT NULL,
  `idCreator` int NOT NULL,
  `sourceParameters` json DEFAULT NULL,
  PRIMARY KEY (`idVideoSource`),
  KEY `fk_VideoSources_users1_idx` (`idCreator`),
  CONSTRAINT `fk_VideoSources_users1` FOREIGN KEY (`idCreator`) REFERENCES `users` (`idUser`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-03-17  9:12:40
