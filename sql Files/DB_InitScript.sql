-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema mechlabenviroment
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mechlabenviroment
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mechlabenviroment` DEFAULT CHARACTER SET utf8mb3 ;
USE `mechlabenviroment` ;

-- -----------------------------------------------------
-- Table `mechlabenviroment`.`controlstypes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`controlstypes` (
  `idControlsTypes` INT NOT NULL AUTO_INCREMENT,
  `TypeName` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idControlsTypes`))
ENGINE = InnoDB
AUTO_INCREMENT = 4
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`users` (
  `idUser` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(45) NOT NULL,
  `pwd` VARCHAR(45) NOT NULL,
  `email` VARCHAR(45) NULL DEFAULT NULL,
  `registerdate` TIMESTAMP NULL DEFAULT NULL,
  `telegrambotToken` VARCHAR(255) NULL DEFAULT NULL,
  `userState` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idUser`),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 3
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`dashboardcontrolt`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`dashboardcontrolt` (
  `idControl` INT NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(45) NULL DEFAULT NULL,
  `idType` INT NOT NULL,
  `idUser` INT NOT NULL,
  `parameters` JSON NULL DEFAULT NULL,
  PRIMARY KEY (`idControl`),
  INDEX `fk_dashboardControlT_ControlsTypes1_idx` (`idType` ASC) VISIBLE,
  INDEX `fk_dashboardControlT_users1_idx` (`idUser` ASC) VISIBLE,
  CONSTRAINT `fk_dashboardControlT_ControlsTypes1`
    FOREIGN KEY (`idType`)
    REFERENCES `mechlabenviroment`.`controlstypes` (`idControlsTypes`),
  CONSTRAINT `fk_dashboardControlT_users1`
    FOREIGN KEY (`idUser`)
    REFERENCES `mechlabenviroment`.`users` (`idUser`))
ENGINE = InnoDB
AUTO_INCREMENT = 4
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`devicesmodes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`devicesmodes` (
  `idDevicesModes` INT NOT NULL AUTO_INCREMENT,
  `mode` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idDevicesModes`))
ENGINE = InnoDB
AUTO_INCREMENT = 3
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`devicestype`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`devicestype` (
  `idDevicesType` INT NOT NULL AUTO_INCREMENT,
  `type` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idDevicesType`))
ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`supportedprotocols`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`supportedprotocols` (
  `idsupportedProtocols` INT NOT NULL AUTO_INCREMENT,
  `ProtocolName` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idsupportedProtocols`))
ENGINE = InnoDB
AUTO_INCREMENT = 4
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`nodestable`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`nodestable` (
  `idNodesTable` INT NOT NULL AUTO_INCREMENT,
  `nodeName` VARCHAR(45) NULL DEFAULT NULL,
  `nodePath` VARCHAR(45) NULL DEFAULT NULL,
  `idDeviceProtocol` INT NOT NULL,
  `idOwnerUser` INT NOT NULL,
  `connectionParameters` VARCHAR(512) NULL DEFAULT NULL,
  PRIMARY KEY (`idNodesTable`),
  INDEX `fk_NodesTable_supportedProtocols_idx` (`idDeviceProtocol` ASC) VISIBLE,
  INDEX `fk_NodesTable_users1_idx` (`idOwnerUser` ASC) VISIBLE,
  CONSTRAINT `fk_NodesTable_supportedProtocols`
    FOREIGN KEY (`idDeviceProtocol`)
    REFERENCES `mechlabenviroment`.`supportedprotocols` (`idsupportedProtocols`),
  CONSTRAINT `fk_NodesTable_users1`
    FOREIGN KEY (`idOwnerUser`)
    REFERENCES `mechlabenviroment`.`users` (`idUser`))
ENGINE = InnoDB
AUTO_INCREMENT = 22
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`devices`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`devices` (
  `idDevices` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  `idMode` INT NOT NULL,
  `idType` INT NOT NULL,
  `channelPath` VARCHAR(45) NULL DEFAULT NULL,
  `idParentNode` INT NOT NULL,
  PRIMARY KEY (`idDevices`),
  INDEX `fk_Devices_DevicesModes1_idx` (`idMode` ASC) VISIBLE,
  INDEX `fk_Devices_DevicesType1_idx` (`idType` ASC) VISIBLE,
  INDEX `fk_Devices_NodesTable1_idx` (`idParentNode` ASC) VISIBLE,
  CONSTRAINT `fk_Devices_DevicesModes1`
    FOREIGN KEY (`idMode`)
    REFERENCES `mechlabenviroment`.`devicesmodes` (`idDevicesModes`),
  CONSTRAINT `fk_Devices_DevicesType1`
    FOREIGN KEY (`idType`)
    REFERENCES `mechlabenviroment`.`devicestype` (`idDevicesType`),
  CONSTRAINT `fk_Devices_NodesTable1`
    FOREIGN KEY (`idParentNode`)
    REFERENCES `mechlabenviroment`.`nodestable` (`idNodesTable`))
ENGINE = InnoDB
AUTO_INCREMENT = 10
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mechlabenviroment`.`devicesmeasures`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mechlabenviroment`.`devicesmeasures` (
  `idDevicesMeasures` INT NOT NULL AUTO_INCREMENT,
  `value` VARCHAR(45) NULL DEFAULT NULL,
  `uploadDate` TIMESTAMP NULL DEFAULT NULL,
  `idDevice` INT NOT NULL,
  PRIMARY KEY (`idDevicesMeasures`),
  INDEX `fk_DevicesMeasures_Devices1_idx` (`idDevice` ASC) VISIBLE,
  CONSTRAINT `fk_DevicesMeasures_Devices1`
    FOREIGN KEY (`idDevice`)
    REFERENCES `mechlabenviroment`.`devices` (`idDevices`))
ENGINE = InnoDB
AUTO_INCREMENT = 11
DEFAULT CHARACTER SET = utf8mb3;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
