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
-- Dumping data for table `controlstypes`
--

LOCK TABLES `controlstypes` WRITE;
/*!40000 ALTER TABLE `controlstypes` DISABLE KEYS */;
INSERT INTO `controlstypes` VALUES (1,'DIGITALOUTPUT','{\"idDevice\": \"REFERENCE\", \"onCmdStr\": \"FIELD\", \"apperance\": [\"TOGGLESWITCH\", \"BUTTON\"], \"offCmdStr\": \"FIELD\", \"updateCmdStr\": \"FIELD\"}'),(2,'SENSORREAD','{\"idDevice\": \"REFERENCE\", \"lowLimit\": \"NUMBER\", \"apperance\": [\"TEXTVAL\", \"HBAR\", \"YBAR\", \"GAUGE\"], \"highLimit\": \"NUMBER\", \"updateCmdStr\": \"FIELD\"}'),(3,'PLAINTEXT','{\"idDevice\": \"REFERENCE\", \"apperance\": [\"INPUTTEXT\", \"CONSOLE\"], \"updateCmdStr\": \"FIELD\"}'),(4,'DIGITALINPUT','{\"idDevice\": \"REFERENCE\", \"apperance\": [\"LED\"], \"updateCmdStr\": \"FIELD\"}');
/*!40000 ALTER TABLE `controlstypes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `devicesmodes`
--

LOCK TABLES `devicesmodes` WRITE;
/*!40000 ALTER TABLE `devicesmodes` DISABLE KEYS */;
INSERT INTO `devicesmodes` VALUES (1,'PUBLISHER'),(2,'SUBSCRIBER');
/*!40000 ALTER TABLE `devicesmodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `devicestype`
--

LOCK TABLES `devicestype` WRITE;
/*!40000 ALTER TABLE `devicestype` DISABLE KEYS */;
INSERT INTO `devicestype` VALUES (1,'FLOAT'),(2,'STRING'),(3,'INT'),(4,'CAMERA');
/*!40000 ALTER TABLE `devicestype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `supportedprotocols`
--

LOCK TABLES `supportedprotocols` WRITE;
/*!40000 ALTER TABLE `supportedprotocols` DISABLE KEYS */;
INSERT INTO `supportedprotocols` VALUES (2,'MQTT'),(3,'SOCKET');
/*!40000 ALTER TABLE `supportedprotocols` ENABLE KEYS */;
UNLOCK TABLES;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-03-17  9:13:56
