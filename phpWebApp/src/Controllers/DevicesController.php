<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

class DevicesController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/devices
     * Also accepts POST with JSON body for clients that send body (compat with legacy client).
     *
     * Params (query or JSON body):
     *  - pageCount (int)  -> page index (0-based)
     *  - pageSize  (int)  -> page size
     *  - deviceName (string) -> filter devices.name LIKE %deviceName%
     *  - nodeName (string) -> filter nodestable.nodeName LIKE %nodeName%
     *  - idDevices (int) -> optional exact id filter (returns single row in array)
     *
     * Returns array of joined device rows:
     *  idDevices, name, mode, type, channelPath, nodeName, idMode, idType, idParentNode
     */
    public function list(Request $req, Response $res): Response
    {
        // Accept query params or JSON body for compatibility
        $params = $req->getQueryParams();
        if (empty($params)) {
            $body = (array)$req->getParsedBody();
            $params = $body ?: [];
        }

        $page = max(0, (int)($params['pageCount'] ?? $params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['pageSize'] ?? $params['size'] ?? 50)));
        $deviceName = isset($params['deviceName']) ? $params['deviceName'] : null;
        $nodeName = isset($params['nodeName']) ? $params['nodeName'] : null;
        $idDevices = isset($params['idDevices']) ? (int)$params['idDevices'] : null;

        $sql = "SELECT 
                    devices.idDevices,
                    devices.name,
                    devicesmodes.mode,
                    devicestype.type,
                    devices.channelPath,
                    nodestable.nodeName,
                    devices.idMode,
                    devices.idType,
                    devices.idParentNode
                FROM devices
                    INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes
                    INNER JOIN devicestype ON devices.idType = devicestype.idDevicesType
                    INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable
                WHERE 1=1";

        $bindings = [];

        if ($idDevices) {
            $sql .= " AND devices.idDevices = :idDevices";
            $bindings['idDevices'] = $idDevices;
        } else {
            if ($deviceName !== null) {
                $sql .= " AND devices.name LIKE :deviceName";
                $bindings['deviceName'] = '%' . $deviceName . '%';
            }
            if ($nodeName !== null) {
                $sql .= " AND nodestable.nodeName LIKE :nodeName";
                $bindings['nodeName'] = '%' . $nodeName . '%';
            }
            $sql .= " ORDER BY devices.name DESC LIMIT :limit OFFSET :offset";
        }

        try {
            $stmt = $this->db->pdo()->prepare($sql);

            foreach ($bindings as $k => $v) {
                $stmt->bindValue(':' . $k, $v, is_int($v) ? PDO::PARAM_INT : PDO::PARAM_STR);
            }

            if (!$idDevices) {
                $stmt->bindValue(':limit', (int)$size, PDO::PARAM_INT);
                $stmt->bindValue(':offset', (int)($page * $size), PDO::PARAM_INT);
            }

            $stmt->execute();
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Devices list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/device
     * Returns single device with joined fields.
     */
    public function get(Request $req, Response $res): Response
    {
        $params = $req->getQueryParams();
        $id = (int)($params['id'] ?? 0);
        if ($id <= 0) {
            $res->getBody()->write(json_encode(['error' => 'invalid_id']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        $sql = "SELECT 
                    devices.idDevices,
                    devices.name,
                    devicesmodes.mode,
                    devicestype.type,
                    devices.channelPath,
                    nodestable.nodeName,
                    devices.idMode,
                    devices.idType,
                    devices.idParentNode
                FROM devices
                    INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes
                    INNER JOIN devicestype ON devices.idType = devicestype.idDevicesType
                    INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable
                WHERE devices.idDevices = :id LIMIT 1";

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                $res->getBody()->write(json_encode(['error' => 'not_found']));
                return $res->withHeader('Content-Type', 'application/json')->withStatus(404);
            }
            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Devices get error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * POST /api/devices/fetchDeviceById
     * Body: { deviceId }
     * Returns same shape as get()
     */
    public function fetchDeviceById(Request $req, Response $res): Response
    {
        $body = (array)$req->getParsedBody();
        $id = isset($body['deviceId']) ? (int)$body['deviceId'] : 0;
        if ($id <= 0) {
            $res->getBody()->write(json_encode(['error' => 'invalid_deviceId']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }
        return $this->get($req, $res, ['id' => $id]);
    }

    /**
     * POST /api/devices/fetchDevices
     * Body: { pageCount, pageSize, deviceName, nodeName, idDevices (optional) }
     * Returns same shape as list()
     */
    public function fetchDevices(Request $req, Response $res): Response
    {
        return $this->list($req, $res);
    }

    // ----------------------
    // Helpers
    // ----------------------
    private function jsonError(Response $res, string $msg, int $status = 400): Response
    {
        $res->getBody()->write(json_encode(['error' => $msg]));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}
