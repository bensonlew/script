package main

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"strings"
)

// import "time"

//const HOST string = os.Getenv("SG_COM_HOST")
//const PORT string = os.Getenv("SG_COM_PORT")

func searchText(method string, searchTxtStr string, types string, sortFields string) (string, error) {
	query := map[string]string{
		"method":     method,
		"string":     searchTxtStr,
		"types":      types,
		"sort_field": sortFields,
	}
	jsonString, _ := json.Marshal(query)
	// println(string(jsonString))

	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%s", os.Getenv("SG_COM_HOST"), os.Getenv("SG_COM_PORT")))
	if err != nil {
		fmt.Printf("conn server failed, err:%v\n", err)
		return "", err
	}

	_, err = conn.Write([]byte(jsonString))
	if err != nil {
		fmt.Printf("send failed, err:%v\n", err)
		return "", err
	}

	var buf [65536]byte
	n, err := conn.Read(buf[:])
	if err != nil {
		fmt.Printf("read failed:%v\n", err)
		return "", err
	}
	return string(buf[:n]), err

}

func stringInSlice(a string, list []string) bool {
	for _, b := range list {
		if b == a {
			return true
		}
	}
	return false
}

func autoCommand(dirStr string, cmdStr string) {
	// nownviron = map[string]string{
	// 	"dirs": {},
	// 	"files": {},
	// 	"cmds": {}
	// }
	fileCmdList := []string{"less", "cat", "zcat", "nano", "vi", "vim", "emacs", "grep", "head", "tail"}
	ignoreCmdList := []string{"history", "sgf", "sgc", "sgd", "cd", "which", "less", "cat", "zcat", "nano", "vi", "vim", "emacs", "grep", "pwd", "ls", "ll", "mkdir", "rm", "head", "tail", "#"}
	cmdList := strings.Split(cmdStr, " ")
	// println(cmdStr)
	if len(cmdList) < 1 || len(cmdList) > 32 {
		return
	}
	if stringInSlice(cmdList[0], fileCmdList) {
		for i := 1; i < len(cmdList); i++ {
			filePath := cmdList[i]
			if filePath[0:1] == "~" || strings.Contains(filePath[0:1], "/") {
				updateFile(dirStr, filePath)
			}
		}
	}

	// println(cmdList[0])
	// println(cmdStr)
	// println(strings.Contains(cmdStr, "|"))
	if !stringInSlice(cmdList[0], ignoreCmdList) || strings.Contains(cmdStr, "|") {

		if cmdStr[0:1] == "#" {
			return
		}

		updateCmd(dirStr, cmdStr)
	}
	return
}

func updateCmd(dirStr string, cmdStr string) {
	// println("updateCmd")
	var sshClient string = ""
	var sshPort string = ""
	// println(os.Getenv("SSH_CLIENT"))
	if os.Getenv("SSH_CLIENT") != "" {
		sshClient = strings.Split(os.Getenv("SSH_CLIENT"), " ")[0]
		sshPort = strings.Split(os.Getenv("SSH_CLIENT"), " ")[1]
	}

	query := map[string]string{
		"method":     "text_update",
		"types":      "cmds",
		"string":     cmdStr,
		"dir":        dirStr,
		"user":       os.Getenv("USER"),
		"ssh_client": sshClient,
		"ssh_port":   sshPort,
	}
	jsonString, _ := json.Marshal(query)
	// println(string(jsonString))

	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%s", os.Getenv("SG_COM_HOST"), os.Getenv("SG_COM_PORT")))
	if err != nil {
		fmt.Printf("conn server failed, err:%v\n", err)
	}

	_, err = conn.Write([]byte(jsonString))
	if err != nil {
		fmt.Printf("send failed, err:%v\n", err)
	}
	return
}

func updateFile(dirStr string, fileStr string) {
	var sshClient string = ""
	var sshPort string = ""
	// println(os.Getenv("SSH_CLIENT"))
	if os.Getenv("SSH_CLIENT") != "" {
		sshClient = strings.Split(os.Getenv("SSH_CLIENT"), " ")[0]
		sshPort = strings.Split(os.Getenv("SSH_CLIENT"), " ")[1]
	}

	query := map[string]string{
		"method":     "text_update",
		"types":      "file",
		"string":     fileStr,
		"dir":        dirStr,
		"user":       os.Getenv("USER"),
		"ssh_client": sshClient,
		"ssh_port":   sshPort,
	}
	jsonString, _ := json.Marshal(query)
	// println(string(jsonString))

	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%s", os.Getenv("SG_COM_HOST"), os.Getenv("SG_COM_PORT")))
	if err != nil {
		fmt.Printf("conn server failed, err:%v\n", err)
	}

	_, err = conn.Write([]byte(jsonString))
	if err != nil {
		fmt.Printf("send failed, err:%v\n", err)
	}
	return

}

func client(args []string) (n int, err error) {
	// addr := net.ParseIP(HOST)
	// println(addr)
	method := args[1]
	if method == "text_search" {
		types := args[2]
		sortFields := args[3]
		var searchTxtStr string = args[4]
		// searchTxt := args[4:]
		for i := 5; i < len(args); i++ {
			searchTxtStr = fmt.Sprintf("%s %s", searchTxtStr, args[i])
		}
		// search := fmt.Sprintf("%s;%s;%s;%s", method, searchTxtStr, types, sortFields)
		result, _ := searchText(method, searchTxtStr, types, sortFields)
		fmt.Println(result)
	} else if method == "auto_cmd" {
		if len(args) < 4 {

		} else {
			dirStr := args[2]
			var cmdStr string = args[3]
			// cmdList := args[3:]
			for i := 4; i < len(args); i++ {
				cmdStr = fmt.Sprintf("%s %s", cmdStr, args[i])
			}
			autoCommand(dirStr, cmdStr)
		}

	} else {

	}
	return n, err

}

func main() {
	// fmt.Printf("%s\n", age)
	//fmt.Println(s)
	/* println(age)
	fmt.Printf("%s\n", s)
	fmt.Println(s2)
	*/
	// fmt.Println(os.Args)
	// method := os.Args[1]
	client(os.Args)

}
