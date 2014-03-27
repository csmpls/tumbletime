$(function()
            {
                $('#clickme').click(function(){
                    alert('Im going to start processing');
                    $.ajax({
                        url: "/login1",
                        type: "get",
                        datatype:"text",
                        success: function(response){
                            alert(response);
                        }
                    });
                });
            

                $('#clickme2').click(function(){
                    alert($('#email').val());
                    $.ajax({
                        type : 'POST',
                        url : '/login2',      /*{{ url_for("app.login2") }} error */
                        data: $('#email').val(),
                        contentType: 'application/text;charset=UTF-8',
                        success: function(result) {
                            console.log(result);
                        }
                    });
                });

            });



