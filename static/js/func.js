function auth(class_name){
	$.ajax({
		data: $("." + class_name).serialize(),
		url: "/",
		method: "post",
		dataType: "json",
		success: function(data){
			console.log(data);
			if (data.status == "200") {
				document.cookie = "user=" + data.user + ";";
				document.cookie = "secret=" + data.secret + ";";
				location.href = "/";
			}
			else{
				alert(data.error_text);
			}
		}
	});
}

function register(class_name){
	$.ajax({
		data: $("." + class_name).serialize(),
		url: "/register/",
		method: "post",
		dataType: "json",
		success: function(data){
			if (data.status == "200") {
				alert("Вы зарегистрированы");
				location.href = "/";
			}
			else {
				alert(data.error_text)
			}
		}
	});
}

function journal(gid){
	jurl = 'jshow=' + gid;

	current_url = location.href;
	var param_pos = current_url.indexOf('?');

	var param_str = "";
	if (param_pos > -1) {
		//Вытащить строку параметров
		param_str = current_url.substring(param_pos);

		var jurl_pos = param_str.indexOf(jurl);
		if (jurl_pos > -1) {
			if (param_str[jurl_pos - 1] == "&")
				param_str = param_str.replace('&' + jurl, "");
			else if (param_str[jurl_pos - 1] == "?" && param_str[jurl_pos + jurl.length] == "&") {
				param_str = param_str.replace(jurl + '&', "");
			}
			else if (param_str[jurl_pos - 1] == "?") {
				param_str = param_str.replace('?' + jurl, "");
			}
    		$("#" + gid).css('display', 'none');
		}
		else {
			if (param_str[param_str.length - 1] != "?" && param_str[param_str.length - 1] != "&")
				param_str += '&';
			param_str = param_str + jurl;
    		$("#" + gid).css('display', 'block');
		}
	}
	else {
		param_str += '?' + jurl;
    	$("#" + gid).css('display', 'block');
	}

	if (param_str == "")
		param_str = '/';

//	console.log(param_str);
	try {
		history.pushState(null, null, param_str);
		return;
	} catch(e) {}
    history.go();
}

function upjournal(gid){
	$.ajax({
		data: {
			gid: gid,
			act: "update"
		},
		url: "/",
		method: "post",
		dataType: "json",
		success: function(data){
			if (data.status == "200") {
//				alert(1==1);
			}
		}
	});
}
